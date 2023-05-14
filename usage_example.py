from typing import TypedDict
import requests, os, shutil

PORT = 5687

class StartProcessRequest(TypedDict):
    command: str
    args: list[str]
    env: dict[str, str]
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

assert resp.json().get("code") == "success"

# press Ctrl+D, the subprocess exits very sooner
while True:
    import time
    time.sleep(0.5)

