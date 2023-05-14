from __future__ import annotations
from aiohttp import web
import typing
import subprocess
import wisepy2
import asyncio
import psutil
import json
import shlex

PROCESS_OWNERSHIP: dict[int, list[subprocess.Popen[bytes]]] = {}

## Request types

class StartProcessRequest(typing.TypedDict):
    command: str
    args: list[str]
    env: dict[str, str]
    pid: int

class StopProcessRequest(typing.TypedDict):
    subproc_pid: int
    pid: int

def start_subprocess(request: StartProcessRequest):
    command = request["command"]
    args = request["args"]
    env = request["env"]
    pid = request["pid"]
    p = subprocess.Popen([command, *args], env=env, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    attached_pids = PROCESS_OWNERSHIP.setdefault(pid, [])
    attached_pids.append(p)
    return p.pid

def stop_subprocess(request: StopProcessRequest, loop: asyncio.AbstractEventLoop):
    subprocess_pid = request["subproc_pid"]
    pid = request["pid"]
    if pid not in PROCESS_OWNERSHIP:
        return False
    else:
        attached_pids = PROCESS_OWNERSHIP[pid]

        for i, each in enumerate(attached_pids):
            if each.pid == subprocess_pid:
                p = attached_pids[i]
                del attached_pids[i]
                try:
                    p.terminate()
                except:
                    pass

                log("Killing subprocess {} for process {}".format(p.pid, pid), level='warning')

                def force_kill(p: subprocess.Popen[bytes], pid):
                    try:
                        p.kill()
                        log("Force killed subprocess {} for process {}".format(p.pid, pid), level='warning')
                    except:
                        pass

                loop.call_soon_threadsafe(force_kill, p, pid)
                return True
    return False

def show_json(x):
    return json.dumps(x, indent=4, ensure_ascii=False)

def log(msg: str, *, level: typing.Literal['info', 'success', 'error', 'warning']):
    if level == 'info':
        print(wisepy2.Blue(msg))
    elif level == 'error':
        print(wisepy2.Red(msg))
    elif level == 'success':
        print(wisepy2.Green(msg))
    elif level == 'warning':
        print(wisepy2.Yellow(msg))
    else:
        print(msg)

async def monitoring_subprocesses_step():
    to_delete: list[int] = []
    for pid, subprocesses in PROCESS_OWNERSHIP.items():
        if psutil.pid_exists(pid):
            continue
        else:
            to_delete.append(pid)
            for each in subprocesses:
                try:
                    each.terminate()
                except:
                    pass
                log("Killing subprocess {} for dead process {}".format(each.pid, pid), level='warning')

            # TODO: force kill in the next few seconds
            for each in subprocesses:
                try:
                    if each.poll() is None:
                        each.kill()
                except:
                    pass

    for each in to_delete:
        del PROCESS_OWNERSHIP[each]

async def kill_all_subprocesses():
    log("Killing all subprocesses...", level='info')
    for _, subprocesses in PROCESS_OWNERSHIP.items():
        for each in subprocesses:
            try:
                each.terminate()
            except:
                pass

        for each in subprocesses:
            try:
                each.kill()
            except:
                pass


def subproc_mgr(*, port: int = 5687, period: float = 0.35):
    """
    port: port that the service is deployed on
    period: how often the service checks the lifetime of subprocesses
    """
    period = min(0.1, period)
    app = web.Application()

    # the index page shows the current status of the subprocesses
    async def index(req):
        return web.json_response({str(pid): [p.pid for p in sps] for pid, sps in PROCESS_OWNERSHIP.items()})

    async def spawn(req: web.Request):
        request: StartProcessRequest = await req.json()
        # to avoid thread safety issues as the web framework used here is not mandatory
        command = shlex.join([request["command"], *request["args"]])
        try:
            pid = start_subprocess(request)
            log("Started subprocess: {}".format(command), level='success')
            return web.json_response({"code": "success", "subproc_pid": pid})
        except Exception as e:
            log("Failed to start subprocess: {}".format(command), level='error')
            log("Error: {}".format(e), level='error')
            return web.json_response({"code": "failure"})

    async def stop(req: web.Request):
        request: StopProcessRequest = await req.json()
        found = stop_subprocess(request, asyncio.get_running_loop())
        return web.json_response({"code": "success" if found else 'failure'})

    app.router.add_get("/", index)
    app.router.add_post("/spawn", spawn)
    app.router.add_post("/stop", stop)

    async def serve():
        _scan_period = period
        runner = web.AppRunner(app)

        try:
            log("Starting subprocess manager on port %d..." % port, level='info')
            await runner.setup()
            site = web.TCPSite(runner, "localhost", port)
            await site.start()

            while True:
                await asyncio.sleep(_scan_period)
                await monitoring_subprocesses_step()

        finally:
            await runner.cleanup()
            await kill_all_subprocesses()

    return asyncio.run(serve())
