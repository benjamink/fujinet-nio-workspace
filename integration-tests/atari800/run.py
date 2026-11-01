#!/usr/bin/env python3
"""Boot a native NIO stress guest on the real Atari800 NetSIO path, headlessly."""
import argparse
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--emulator', type=Path, default=ROOT / 'build/atari800-netsio-src/src/atari800')
    p.add_argument('--firmware', type=Path, default=ROOT / 'repos/fujinet-nio/build/atari-fujibus-netsio-debug/fujinet-nio')
    p.add_argument('--rom', type=Path, default=Path(os.environ.get('ATARI_OS_ROMS', '')) / 'REV02.ROM')
    p.add_argument('--ack-gap-us', type=int, default=250)
    p.add_argument('--timeout', type=int, default=180)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    if not 0 <= args.ack_gap_us <= 100000:
        p.error('ack gap must be between 0 and 100000 microseconds')
    for path in (args.emulator, args.firmware, args.rom, ROOT / 'repos/fujinet-nio-lib/build/fujinet-nio-atari.lib'):
        if not path.is_file():
            raise SystemExit(f'Missing {path}; source scripts/env.sh and build the required target')
    out = args.out.resolve() if args.out else Path(tempfile.mkdtemp(prefix='nio-atari800-'))
    out.mkdir(parents=True, exist_ok=True)
    stage = out / 'stage'
    data = out / 'fujinet-data'
    stage.mkdir()
    (data / 'boot/atari').mkdir(parents=True)
    xex = stage / 'AUTORUN.XEX'
    subprocess.run(['cl65', '-t', 'atari', '-O', '-I', str(ROOT / 'repos/fujinet-nio-lib/include'),
                    '-o', str(xex), str(HERE / 'traffic.c'), str(HERE / 'traffic_dli.s'),
                    str(ROOT / 'repos/fujinet-nio-lib/build/fujinet-nio-atari.lib')], check=True, cwd=out)
    atr = data / 'boot/atari/autorun.atr'
    subprocess.run(['dir2atr', '-b', 'PicoBoot406', str(atr), str(stage)], check=True, cwd=out)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    (data / 'fujinet.yaml').write_text(
        f'netsio:\n  enabled: true\n  host: 127.0.0.1\n  port: {port}\n'
        'boot:\n  mode: config\n  config_uri: persist:/boot/atari/autorun.atr\n  readonly: true\n'
        f'atari_sio:\n  ack_gap_us: {args.ack_gap_us}\n')
    result = out / 'result.txt'
    env = os.environ.copy()
    env['NIO_ATARI800_RESULT'] = str(result)
    cmd = [str(args.emulator.resolve()), '-config', str(out / 'atari800.cfg'), '-xl', '-pal',
           '-xlxe_rom', str(args.rom.resolve()), '-nobasic', '-nopatch', '-netsio', str(port)]
    print(f'Atari800 evidence: {out}', flush=True)
    processes = []
    with (out / 'atari800.log').open('w') as emu_log, (out / 'nio.log').open('w') as nio_log:
        try:
            processes.append(subprocess.Popen(cmd, cwd=out, env=env, stdout=emu_log, stderr=subprocess.STDOUT))
            # Atari800's -netsio waits up to five seconds for DEVICE_CONNECTED.
            time.sleep(.25)
            processes.append(subprocess.Popen([str(args.firmware.resolve())], cwd=out,
                                              stdout=nio_log, stderr=subprocess.STDOUT))
            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                if result.exists() and processes[0].poll() is not None:
                    break
                if any(proc.poll() is not None for proc in processes):
                    raise RuntimeError('emulator or firmware exited before the guest completed')
                time.sleep(.1)
            else:
                raise RuntimeError('guest timed out; inspect the captured emulator and firmware logs')
            text = result.read_text().strip()
            print(text)
            match = re.fullmatch(r'init=(\d+) completed=(\d+) failures=(\d+) slow=(\d+) dli=(\d+)', text)
            if not match:
                raise RuntimeError('guest returned an invalid result')
            init, completed, failures, slow, dli = map(int, match.groups())
            if (init, completed, failures, slow) != (0, 200, 0, 0) or not dli:
                raise RuntimeError('guest reported an error, incomplete run, slow call, or no DLI')
        finally:
            for proc in reversed(processes):
                if proc.poll() is None:
                    proc.terminate()
            for proc in reversed(processes):
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
    print('Atari800 native SIO workload passed')

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'Atari800 test failed: {exc}', file=sys.stderr)
        sys.exit(1)
