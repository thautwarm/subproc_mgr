from typing import TypedDict
import requests, os, shutil

PORT = 5687

class StartProcessRequest(TypedDict):
    command: str
    args: list[str]
    env: dict[str, str]
    pid: int

class StopProcessRequest(TypedDict):
    subproc_pid: int
    pid: int

# start python -m http.server
resp = requests.post(
    f"http://localhost:{PORT}/spawn",
    json=StartProcessRequest(
        command=shutil.which("python") or "python",
        args=['-m', 'http.server'],
        env=dict(os.environ),
        pid=os.getpid()
    )
)

d = resp.json()
assert resp.json().get("code") == "success"

# press Ctrl+D, the subprocess exits very sooner
import time
start = time.time()

while time.time() - start < 5:
    time.sleep(0.5)

r = requests.post(
    f"http://localhost:{PORT}/stop",
    json=StopProcessRequest(
        subproc_pid=d['subproc_pid'],
        pid=os.getpid()
    )
)

assert r.json().get("code") == "success"
