#!/usr/bin/env python3
import json
import os
import socket
import struct
import subprocess
import tempfile
from pathlib import Path
import yaml

SOCK = "/tmp/mcf-hermes-relay.sock"
HERMES = "/home/ubuntu/.local/bin/hermes"
ALLOWED_UIDS = {994, 1000}
ENV = os.environ.copy()
ENV.update({
    "HOME": "/home/ubuntu",
    "USER": "ubuntu",
    "LOGNAME": "ubuntu",
    "PATH": "/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin",
    "DISPLAY": ":10",
    "XAUTHORITY": "/home/ubuntu/.Xauthority",
    "XDG_RUNTIME_DIR": "/run/user/1000",
    "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
})
CONFIG = Path('/home/ubuntu/.hermes/config.yaml')

PROBE = "Reply with exactly HERMES_READY and nothing else."
HELLO = """Execute the first canonical Hermes Operator GUI validation on this Linux VPS.
Use ONLY the computer_use toolset and normal visible GUI interaction. Do not use terminal, shell, filesystem APIs, browser APIs, DOM, CDP, backend calls, developer tools, or credentials.

IMPORTANT: the active local model is text-only. For every computer_use capture, use mode=\"ax\" so you operate from the Linux accessibility tree only. Do not request SOM or vision screenshots.

1. Confirm Brave and the graphical editor are initially closed. If either is already open, return PRECONDITION_FAILED and stop.
2. Open Brave through normal graphical desktop interaction.
3. In Brave navigate to https://chatgpt.com through normal GUI interaction.
4. If ChatGPT is not already authenticated or asks for login, password, code, or authentication, STOP without entering credentials and return exactly AUTH_REQUIRED.
5. If authenticated, start a new ChatGPT conversation.
6. Type exactly: Hello World
7. Send it and wait until ChatGPT has completely finished responding.
8. Read the entire response through the accessibility tree, scrolling as needed, and understand it semantically.
9. Open a simple graphical text editor through the GUI.
10. Write a short report in your own words using exactly these headings:
MISSÃO
RESPOSTA ENTENDIDA
AVALIAÇÃO
RESULTADO: SUCESSO
11. Save it as /home/ubuntu/Hermes-Hello-World.txt using only the editor's graphical Save/Save As flow.
12. Verify through the GUI that the file is saved and the report content is present.
13. Return a concise final response beginning HELLO_WORLD_GUI_OK:. Do not start any other objective.
"""

OPS = {
    "version": ([HERMES, "--version"], 120),
    "doctor": ([HERMES, "doctor"], 120),
    "status": ([HERMES, "status"], 120),
    "config_model": ([HERMES, "config", "get", "model", "--json"], 120),
    "computer_use_status": ([HERMES, "computer-use", "status"], 120),
    "computer_use_doctor": ([HERMES, "computer-use", "doctor"], 120),
    "cognitive_probe": ([HERMES, "-z", PROBE, "--ignore-rules"], 300),
    "hello_world_gui": ([HERMES, "-z", HELLO, "-t", "computer_use", "--ignore-rules"], 1200),
}


def configure_local_provider():
    cfg = yaml.safe_load(CONFIG.read_text()) if CONFIG.exists() else {}
    if not isinstance(cfg, dict):
        cfg = {}
    model = cfg.get('model')
    if not isinstance(model, dict):
        model = {}
    model.update({
        'default': 'qwen3-4b-instruct-2507',
        'provider': 'custom',
        'base_url': 'http://127.0.0.1:8080/v1',
        'api_key': 'no-key',
        'context_length': 65536,
    })
    cfg['model'] = model
    fd, tmp = tempfile.mkstemp(prefix='config.', suffix='.yaml', dir=str(CONFIG.parent))
    os.close(fd)
    Path(tmp).write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG)
    return {'ok': True, 'model': {k: ('REDACTED' if k == 'api_key' else v) for k, v in model.items()}}


def prepare_run():
    # Test-fixture cleanup only: ensure the two mission apps start closed.
    for pattern in ['brave-browser', 'mousepad', 'xed', 'gedit']:
        subprocess.run(['pkill', '-u', '1000', '-f', pattern], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {'ok': True, 'prepared': True}


def execute(req):
    op = req.get("op")
    if op == 'configure_local_provider':
        return configure_local_provider()
    if op == 'prepare_run':
        return prepare_run()
    if op not in OPS:
        return {"ok": False, "error": "op_not_allowed"}
    cmd, timeout = OPS[op]
    try:
        cp = subprocess.run(cmd, env=ENV, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=timeout)
        return {"ok": cp.returncode == 0, "returncode": cp.returncode,
                "output": cp.stdout[-30000:]}
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        return {"ok": False, "error": "timeout", "output": out[-30000:]}

try:
    os.unlink(SOCK)
except FileNotFoundError:
    pass
srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
srv.bind(SOCK)
os.chmod(SOCK, 0o666)
srv.listen(8)
while True:
    conn, _ = srv.accept()
    try:
        _, uid, _ = struct.unpack("3i", conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if uid not in ALLOWED_UIDS:
            conn.sendall(b'{"ok":false,"error":"peer_not_allowed"}\n')
            continue
        data = b""
        while b"\n" not in data and len(data) < 65536:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        try:
            req = json.loads(data.split(b"\n", 1)[0].decode("utf-8"))
            result = execute(req)
        except Exception as exc:
            result = {"ok": False, "error": type(exc).__name__, "detail": str(exc)[:500]}
        conn.sendall((json.dumps(result) + "\n").encode("utf-8"))
    finally:
        conn.close()
