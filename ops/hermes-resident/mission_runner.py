#!/usr/bin/env python3
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path('/home/ubuntu')
HERMES = HOME / '.local/bin/hermes'
STATE_ROOT = HOME / '.local/state/hermes-operator'
ENV = os.environ.copy()
ENV.update({
    'HOME': str(HOME),
    'USER': 'ubuntu',
    'LOGNAME': 'ubuntu',
    'PATH': '/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin',
    'DISPLAY': ':10',
    'XAUTHORITY': '/home/ubuntu/.Xauthority',
    'XDG_RUNTIME_DIR': '/run/user/1000',
    'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/1000/bus',
    'PYTHONUNBUFFERED': '1',
    'HERMES_STREAM_READ_TIMEOUT': '1800',
})


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    os.replace(tmp, path)


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text())
    except Exception:
        return {} if default is None else default


class Runner:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.dir = STATE_ROOT / 'jobs' / job_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.dir / 'state.json'
        self.current_path = STATE_ROOT / 'current.json'
        self.log_path = self.dir / 'runner.log'
        self.stop_path = self.dir / 'STOP'
        self.state = {
            'mission_id': 'MCF-HERMES-PC-002',
            'job_id': job_id,
            'status': 'RUNNING',
            'phase': 'BOOTSTRAP',
            'started_at': now(),
            'last_progress_at': now(),
            'updated_at': now(),
            'result': None,
            'failure': None,
            'gate': None,
            'attempt': 0,
            'consecutive_successes': 0,
            'pid': os.getpid(),
            'pgid': os.getpgrp(),
            'evidence_dir': str(self.dir),
        }
        self.persist()

    def persist(self):
        self.state['updated_at'] = now()
        atomic_json(self.state_path, self.state)
        atomic_json(self.current_path, self.state)

    def log(self, msg):
        line = f"{now()} {msg}"
        with self.log_path.open('a') as f:
            f.write(line + '\n')
        print(line, flush=True)

    def progress(self, phase=None, **fields):
        if phase:
            self.state['phase'] = phase
        self.state['last_progress_at'] = now()
        self.state.update(fields)
        self.persist()

    def finish(self, status, result=None, failure=None, gate=None):
        self.state.update({
            'status': status,
            'result': result,
            'failure': failure,
            'gate': gate,
            'finished_at': now(),
        })
        self.persist()
        self.log(f"FINISH status={status} result={result} failure={failure} gate={gate}")

    def stop_requested(self):
        return self.stop_path.exists()

    def discover_yaml_python(self):
        candidates = [
            HOME / '.hermes/venv/bin/python',
            HOME / '.hermes/hermes-agent/.venv/bin/python',
            Path('/usr/bin/python3'),
        ]
        for p in candidates:
            if not p.exists():
                continue
            cp = subprocess.run([str(p), '-c', 'import yaml'], env=ENV,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if cp.returncode == 0:
                return str(p)
        raise RuntimeError('no_python_with_yaml')

    def configure_provider(self):
        py = self.discover_yaml_python()
        code = r'''
from pathlib import Path
import os,tempfile,yaml,json
p=Path('/home/ubuntu/.hermes/config.yaml')
cfg=yaml.safe_load(p.read_text()) if p.exists() else {}
if not isinstance(cfg,dict): cfg={}
model=cfg.get('model')
if not isinstance(model,dict): model={}
model.update({
  'default':'qwen3.5-2b',
  'provider':'custom',
  'base_url':'http://127.0.0.1:8080/v1',
  'api_key':'no-key',
  'context_length':65536,
})
cfg['model']=model
p.parent.mkdir(parents=True,exist_ok=True)
fd,tmp=tempfile.mkstemp(prefix='config.',suffix='.yaml',dir=str(p.parent)); os.close(fd)
Path(tmp).write_text(yaml.safe_dump(cfg,sort_keys=False,allow_unicode=True))
os.chmod(tmp,0o600); os.replace(tmp,p)
print(json.dumps({k:('REDACTED' if k=='api_key' else v) for k,v in model.items()}))
'''
        cp = subprocess.run([py, '-c', code], env=ENV, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        self.log('provider_config=' + cp.stdout.strip()[-2000:])
        if cp.returncode != 0:
            raise RuntimeError('provider_config_failed')

    def provider_health(self):
        cp = subprocess.run(['curl','-fsS','--max-time','5','http://127.0.0.1:8080/health'],
                            env=ENV, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return cp.returncode == 0 and 'ok' in cp.stdout.lower()

    def diagnostics(self, name):
        p = self.dir / f'diagnostic-{name}-{int(time.time())}.txt'
        cmds = [
            ['ps','-eo','pid,ppid,etimes,%cpu,%mem,stat,args'],
            ['free','-h'],
            ['df','-h','/'],
            ['curl','-sS','--max-time','3','http://127.0.0.1:8080/health'],
        ]
        with p.open('w') as f:
            for cmd in cmds:
                f.write('$ ' + ' '.join(cmd) + '\n')
                try:
                    cp = subprocess.run(cmd, env=ENV, text=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, timeout=10)
                    out = cp.stdout
                    # sanitize common secret-like material defensively
                    for token in ['Authorization:', 'Bearer ']:
                        if token in out:
                            out = out.replace(token, token + 'REDACTED ')
                    f.write(out[-30000:] + '\n')
                except Exception as e:
                    f.write(type(e).__name__ + '\n')
        self.log(f'diagnostic={p}')

    def run_hermes(self, label, prompt, toolset=None, hard_timeout=1200, quiet_grace=240):
        out_path = self.dir / f'{label}.log'
        cmd = [str(HERMES), '-z', prompt]
        if toolset:
            cmd += ['-t', toolset]
        cmd += ['--ignore-rules']
        self.progress(phase=label.upper())
        self.log('launch=' + label)
        with out_path.open('wb') as f:
            proc = subprocess.Popen(cmd, env=ENV, stdout=f, stderr=subprocess.STDOUT,
                                    start_new_session=True)
        start = time.monotonic()
        last_size = 0
        last_change = start
        diag_done = False
        while True:
            if self.stop_requested():
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=15)
                raise RuntimeError('emergency_stop')
            rc = proc.poll()
            try:
                size = out_path.stat().st_size
            except FileNotFoundError:
                size = 0
            if size != last_size:
                last_size = size
                last_change = time.monotonic()
                self.progress()
            elapsed = time.monotonic() - start
            quiet = time.monotonic() - last_change
            if rc is not None:
                break
            if quiet > quiet_grace and not diag_done:
                self.state['watchdog'] = {
                    'state': 'WAITING_NO_OUTPUT',
                    'observed_at': now(),
                    'quiet_seconds': int(quiet),
                    'hard_deadline_seconds': hard_timeout,
                }
                self.persist()
                self.diagnostics(label)
                diag_done = True
            if elapsed > hard_timeout:
                self.diagnostics(label + '-timeout')
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                    proc.wait(timeout=15)
                except Exception:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except Exception:
                        pass
                raise TimeoutError(label)
            time.sleep(5)
        text = out_path.read_text(errors='replace')[-50000:]
        self.log(f'exit={label} rc={rc} bytes={len(text)}')
        if rc != 0:
            raise RuntimeError(f'{label}_rc_{rc}')
        return text.strip()

    def close_test_apps(self):
        for pattern in ['brave-browser', '/opt/brave.com/brave/brave', 'mousepad', 'gedit', 'xed']:
            subprocess.run(['pkill','-u','1000','-f',pattern], env=ENV,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)

    def verify_report(self, report: Path):
        if not report.exists() or report.stat().st_size < 40:
            return False, 'report_missing_or_small'
        text = report.read_text(errors='replace')
        for heading in ['MISSÃO','RESPOSTA ENTENDIDA','AVALIAÇÃO','RESULTADO: SUCESSO']:
            if heading not in text:
                return False, f'missing_heading_{heading}'
        cp = subprocess.run(['sha256sum',str(report)], text=True, stdout=subprocess.PIPE, env=ENV)
        return True, cp.stdout.split()[0] if cp.stdout else 'sha_unavailable'

    def qualification_prompt(self, attempt, report):
        return f'''Execute Hermes Operator qualification attempt {attempt} on this Linux VPS.

Use ONLY the computer_use toolset and ordinary visible GUI interaction for the user journey. Do not use terminal, shell, filesystem APIs, browser APIs, DOM, CDP, developer tools, backend calls, or credentials to perform the journey.

The local model is text-only. For every computer_use capture/observation, explicitly use accessibility-tree mode (AX) rather than SOM or screenshot vision.

Starting condition: Brave and the graphical text editor are closed. The ChatGPT session must already be authenticated by the human.

Mission:
1. Open Brave through the normal graphical desktop interface.
2. Navigate visibly to https://chatgpt.com.
3. If ChatGPT is not already authenticated, authentication expired, or any login/password/code/captcha is requested, do not enter credentials. Stop and return exactly AUTH_REQUIRED.
4. If authenticated, start a new ChatGPT conversation.
5. Type exactly: Hello World
6. Send it and wait until ChatGPT has completely finished its response.
7. Read the entire response through the GUI/accessibility tree, scrolling if necessary, and understand it semantically.
8. Open a simple graphical text editor through the normal GUI.
9. Write a short report in your own words with exactly these headings on separate lines:
MISSÃO
RESPOSTA ENTENDIDA
AVALIAÇÃO
RESULTADO: SUCESSO
10. Save it through the graphical Save/Save As interface as:
{report}
11. Verify through the GUI that the report content is present and the file is saved.
12. Return a concise final response beginning exactly with HELLO_WORLD_GUI_OK: and summarize completion.

Do not start any other objective. If a reversible GUI problem occurs, re-observe, diagnose and recover safely rather than repeating blindly.'''

    def run(self):
        try:
            if not HERMES.exists():
                raise RuntimeError('hermes_missing')
            self.progress('PROVIDER_CHECK')
            if not self.provider_health():
                raise RuntimeError('local_provider_unhealthy')
            self.configure_provider()

            cognitive = self.run_hermes(
                'cognitive-probe',
                'Reply with exactly HERMES_READY and nothing else.',
                hard_timeout=300,
                quiet_grace=120,
            )
            if 'HERMES_READY' not in cognitive:
                raise RuntimeError('cognitive_probe_failed')

            gui_probe = self.run_hermes(
                'computer-use-probe',
                'Use the computer_use tool exactly once to observe the current Linux desktop in AX/accessibility-tree mode. Do not click, type, open, close, or modify anything. Then reply with exactly GUI_PROBE_OK.',
                toolset='computer_use',
                hard_timeout=420,
                quiet_grace=180,
            )
            if 'GUI_PROBE_OK' not in gui_probe:
                raise RuntimeError('computer_use_probe_failed')

            consecutive = 0
            max_attempts = 6
            for attempt in range(1, max_attempts + 1):
                self.state['attempt'] = attempt
                self.state['consecutive_successes'] = consecutive
                self.persist()
                self.close_test_apps()
                report = HOME / f'Hermes-Hello-World-attempt{attempt}.txt'
                try:
                    report.unlink()
                except FileNotFoundError:
                    pass
                try:
                    out = self.run_hermes(
                        f'hello-world-attempt-{attempt}',
                        self.qualification_prompt(attempt, report),
                        toolset='computer_use',
                        hard_timeout=1200,
                        quiet_grace=240,
                    )
                except (RuntimeError, TimeoutError) as e:
                    self.log(f'attempt={attempt} reversible_failure={e}')
                    consecutive = 0
                    self.state['consecutive_successes'] = 0
                    self.persist()
                    if self.stop_requested():
                        raise
                    continue
                if 'AUTH_REQUIRED' in out:
                    self.finish('HUMAN_GATE', result='BLOCKED', gate=f'CHATGPT_AUTH_REQUIRED_ATTEMPT_{attempt}')
                    return 2
                if 'HELLO_WORLD_GUI_OK:' not in out:
                    self.log(f'attempt={attempt} verdict_missing')
                    consecutive = 0
                    continue
                ok, proof = self.verify_report(report)
                if not ok:
                    self.log(f'attempt={attempt} report_verify_failed={proof}')
                    consecutive = 0
                    continue
                consecutive += 1
                self.state['consecutive_successes'] = consecutive
                self.state.setdefault('proofs', []).append({
                    'attempt': attempt,
                    'report': str(report),
                    'sha256': proof,
                    'verified_at': now(),
                })
                self.progress(phase=f'ATTEMPT_{attempt}_VERIFIED')
                self.log(f'attempt={attempt} PASS consecutive={consecutive} sha256={proof}')
                if consecutive >= 3:
                    self.finish('SUCCEEDED', result='THREE_CONSECUTIVE_RUNS_PASS')
                    return 0
            self.finish('FAILED', result='QUALIFICATION_NOT_MET', failure='max_attempts_without_three_consecutive_successes')
            return 1
        except Exception as e:
            if str(e) == 'emergency_stop':
                self.finish('ABORTED', result='STOPPED', failure='emergency_stop')
                return 130
            self.diagnostics('fatal')
            self.finish('FAILED', result='RUNTIME_FAILURE', failure=f'{type(e).__name__}:{e}')
            return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--job-id', required=True)
    args = ap.parse_args()
    runner = Runner(args.job_id)
    rc = runner.run()
    raise SystemExit(rc)

if __name__ == '__main__':
    main()
