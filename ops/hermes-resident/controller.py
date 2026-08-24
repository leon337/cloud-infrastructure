#!/usr/bin/env python3
import json
import os
import signal
import socket
import struct
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path('/home/ubuntu')
BASE = HOME / '.local/share/hermes-resident'
STATE_ROOT = HOME / '.local/state/hermes-operator'
RUNNER = BASE / 'mission_runner.py'
SOCK = '/tmp/hermes-operator-control.sock'
ALLOWED_UIDS = {994, 1000}


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    os.replace(tmp, path)


def load_current():
    p = STATE_ROOT / 'current.json'
    if not p.exists():
        return {'status':'IDLE','mission_id':'MCF-HERMES-PC-002'}
    try:
        state = json.loads(p.read_text())
    except Exception as e:
        return {'status':'ERROR','error':'state_unreadable','detail':str(e)[:200]}
    pid = state.get('pid')
    if state.get('status') == 'RUNNING' and pid:
        try:
            os.kill(int(pid), 0)
            state['process_alive'] = True
        except Exception:
            state['process_alive'] = False
            state['status'] = 'FAILED'
            state['failure'] = state.get('failure') or 'runner_process_missing'
            state['updated_at'] = now()
            atomic_json(p, state)
    return state


def start_job():
    cur = load_current()
    if cur.get('status') == 'RUNNING' and cur.get('process_alive', True):
        return {'ok':False,'error':'job_already_running','state':cur}
    if not RUNNER.exists():
        return {'ok':False,'error':'runner_missing'}
    job_id = 'MCF-HERMES-PC-002-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    job_dir = STATE_ROOT / 'jobs' / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    launcher_log = (job_dir / 'launcher.log').open('ab', buffering=0)
    proc = subprocess.Popen(
        ['/usr/bin/python3', str(RUNNER), '--job-id', job_id],
        cwd=str(HOME),
        stdin=subprocess.DEVNULL,
        stdout=launcher_log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env={**os.environ,
             'HOME':'/home/ubuntu','USER':'ubuntu','LOGNAME':'ubuntu',
             'PATH':'/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin',
             'DISPLAY':':10','XAUTHORITY':'/home/ubuntu/.Xauthority',
             'XDG_RUNTIME_DIR':'/run/user/1000',
             'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1000/bus'},
    )
    bootstrap = {
        'mission_id':'MCF-HERMES-PC-002',
        'job_id':job_id,
        'status':'RUNNING',
        'phase':'LAUNCHING',
        'started_at':now(),
        'last_progress_at':now(),
        'updated_at':now(),
        'pid':proc.pid,
        'pgid':proc.pid,
        'result':None,'failure':None,'gate':None,
        'evidence_dir':str(job_dir),
    }
    atomic_json(job_dir / 'state.json', bootstrap)
    atomic_json(STATE_ROOT / 'current.json', bootstrap)
    return {'ok':True,'job_id':job_id,'pid':proc.pid,'state':bootstrap}


def stop_job():
    cur = load_current()
    if cur.get('status') != 'RUNNING':
        return {'ok':True,'stopped':False,'reason':'no_running_job','state':cur}
    job_id = cur.get('job_id')
    if job_id:
        p = STATE_ROOT / 'jobs' / job_id / 'STOP'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(now() + '\n')
    pgid = cur.get('pgid') or cur.get('pid')
    if pgid:
        try:
            os.killpg(int(pgid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception as e:
            return {'ok':False,'error':'stop_signal_failed','detail':str(e)[:200]}
    return {'ok':True,'stopped':True,'job_id':job_id}


def runtime():
    def health():
        try:
            cp = subprocess.run(['curl','-fsS','--max-time','3','http://127.0.0.1:8080/health'],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
            return cp.returncode == 0, cp.stdout.strip()[:200]
        except Exception as e:
            return False, type(e).__name__
    h, detail = health()
    return {
        'ok': True,
        'controller_pid': os.getpid(),
        'socket': SOCK,
        'provider_healthy': h,
        'provider_detail': detail,
        'runner_present': RUNNER.exists(),
        'state_root': str(STATE_ROOT),
        'mission_id':'MCF-HERMES-PC-002',
    }


def evidence(req):
    cur = load_current()
    job_id = req.get('job_id') or cur.get('job_id')
    if not job_id:
        return {'ok':False,'error':'no_job'}
    d = STATE_ROOT / 'jobs' / str(job_id)
    if not d.is_dir():
        return {'ok':False,'error':'job_not_found'}
    files=[]
    for p in sorted(d.iterdir()):
        if p.is_file():
            files.append({'name':p.name,'bytes':p.stat().st_size,'mtime':p.stat().st_mtime})
    return {'ok':True,'job_id':job_id,'files':files,'state':load_current() if cur.get('job_id')==job_id else None}


def handle(req):
    op = req.get('op')
    if op == 'ping':
        return {'ok':True,'pong':True,'at':now()}
    if op == 'runtime':
        return runtime()
    if op == 'status':
        return {'ok':True,'state':load_current()}
    if op == 'start':
        return start_job()
    if op == 'stop':
        return stop_job()
    if op == 'evidence':
        return evidence(req)
    return {'ok':False,'error':'op_not_allowed'}


def serve():
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        os.unlink(SOCK)
    except FileNotFoundError:
        pass
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK)
    os.chmod(SOCK, 0o666)
    srv.listen(16)
    while True:
        conn, _ = srv.accept()
        try:
            _, uid, _ = struct.unpack('3i', conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if uid not in ALLOWED_UIDS:
                conn.sendall(b'{"ok":false,"error":"peer_not_allowed"}\n')
                continue
            data=b''
            while b'\n' not in data and len(data)<65536:
                chunk=conn.recv(4096)
                if not chunk: break
                data += chunk
            try:
                req=json.loads(data.split(b'\n',1)[0].decode('utf-8'))
                res=handle(req)
            except Exception as e:
                res={'ok':False,'error':type(e).__name__,'detail':str(e)[:500]}
            conn.sendall((json.dumps(res,ensure_ascii=False)+'\n').encode('utf-8'))
        finally:
            conn.close()

if __name__ == '__main__':
    serve()
