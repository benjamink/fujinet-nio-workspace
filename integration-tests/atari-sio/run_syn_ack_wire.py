#!/usr/bin/env python3
"""Test a specified SYN-ACK WIRE checkout against the NIO workspace, headlessly."""
import argparse
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

workspace = Path(os.environ['NIO_WORKSPACE'])
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--checkout', type=Path, required=True, help='SYN-ACK WIRE repository')
parser.add_argument('--output', type=Path, help='new directory for test logs')
parser.add_argument('--allow-dirty', action='store_true', help='allow tracked changes for development')
args = parser.parse_args()
checkout = args.checkout.resolve()
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'],
                                cwd=checkout, text=True).strip()
if dirty and not args.allow_dirty:
    raise SystemExit('SYN-ACK WIRE checkout has tracked changes; commit them or use --allow-dirty')
sys.path.insert(0, str(workspace / 'repos/nio-config/scripts'))
from atari_shot_netsio import boot
from atari_ui import read_os_screen

with socket.socket() as probe:
    probe.bind(('127.0.0.1', 0))  # choose an unused local port
    port = probe.getsockname()[1]

with tempfile.TemporaryDirectory(prefix='synack-nio-test-') as temporary:
    tmp = Path(temporary)
    if dirty:
        client = checkout / 'client'
    else:
        # Build the exact committed tree, independent of untracked/generated files.
        source = tmp / 'source'
        source.mkdir()
        archive = tmp / 'source.tar'
        with archive.open('wb') as f:
            subprocess.run(['git', 'archive', '--format=tar', revision], cwd=checkout,
                           stdout=f, check=True)
        subprocess.run(['tar', '-xf', str(archive), '-C', str(source)], check=True)
        client = source / 'client'
    build = tmp / 'build'
    output = args.output.resolve() if args.output else tmp / 'output'
    if output.exists():
        raise SystemExit(f'Output directory already exists: {output}')
    output.mkdir()
    (output / 'tested-revision.txt').write_text(revision + ('\ntracked changes present\n' if dirty else '\n'))
    # The deliberately unusable built-in URL makes reaching the server proof
    # that the lobby AppKey was read and used.
    subprocess.run(['make', f'B={build}', 'NIO=1', 'LOBBY_KEY=11',
                    'URL=N:TCP://127.0.0.1:1/', 'atr'], cwd=client, check=True)
    linkmap = (build / 'synack.map').read_text().split('Segment list:', 1)[0]
    for unused in ('fn_packet_parse_info.o', 'fn_legacy_appkey_'):
        if unused in linkmap:
            raise AssertionError(f'Unused library object linked: {unused}')
    appkey = tmp / 'lobby.key'
    appkey.write_text(f'TCP://127.0.0.1:{port}/', encoding='ascii')
    with (output / 'server.log').open('w') as server_log:
        server = subprocess.Popen([sys.executable, '-u', 'serve.py', '--host', '127.0.0.1',
                                   '--port', str(port), '--trace', '--keepalive', '1'],
                                  cwd=client.parent / 'server', stdout=server_log,
                                  stderr=subprocess.STDOUT)
        try:
            time.sleep(1)
            if server.poll() is not None:
                raise RuntimeError('Local game server did not start')

            def inspect(view):
                for _ in range(150):
                    if any('LOBBY OPEN' in row for row in read_os_screen(view.bridge)):
                        break
                    time.sleep(1)
                else:
                    raise AssertionError('Title never received the server lobby status')
                view.screenshot(output / 'title.png')
                view.type('MARK')
                view.key('RETURN')
                for _ in range(30):
                    if any('MARK' in row for row in read_os_screen(view.bridge)):
                        break
                    time.sleep(1)
                else:
                    raise AssertionError('Game did not show the joined player')
                time.sleep(8)
                lines = read_os_screen(view.bridge)
                if any('NO SIGNAL' in row or 'REDIALING' in row for row in lines):
                    raise AssertionError('Connection did not remain live:\n' + '\n'.join(lines))
                server_log.flush()
                trace = (output / 'server.log').read_text()
                if 'joined table 0 as MARK' not in trace or 'disconnected' in trace:
                    raise AssertionError('Server did not record a stable join:\n' + trace)
                if not any('START WITH HOW MANY SEATS' in row for row in lines):
                    raise AssertionError('Host seat-count prompt not shown:\n' + '\n'.join(lines))
                view.key('2')
                for _ in range(20):
                    server_log.flush()
                    trace = (output / 'server.log').read_text()
                    if '(MARK) sent S 02' in trace:
                        break
                    time.sleep(1)
                else:
                    raise AssertionError('Server did not receive the seat-count answer:\n' + trace)
                time.sleep(2)
                view.screenshot(output / 'game.png')
                view.key('ESC')
                for _ in range(20):
                    if any('Y/N' in row for row in read_os_screen(view.bridge)):
                        break
                    time.sleep(1)
                else:
                    raise AssertionError('Log-off confirmation did not appear')
                view.key('Y')
                for _ in range(30):
                    if any('TYPE A HANDLE' in row for row in read_os_screen(view.bridge)):
                        break
                    time.sleep(1)
                else:
                    raise AssertionError('Log-off did not return to the title')
                view.key('RETURN')
                for _ in range(30):
                    server_log.flush()
                    trace = (output / 'server.log').read_text()
                    if trace.count('joined table 0 as MARK') >= 2:
                        break
                    time.sleep(1)
                else:
                    raise AssertionError('Player could not rejoin after log-off:\n' + trace)
                print('Atari NIO: joined, started, logged off and rejoined')

            boot(build / 'syn-ack-wire-atari.atr', inspect,
                 data=[('FujiNet/0001010b.key', appkey)], out=output / 'boot')
        finally:
            server.terminate()
            server.wait(timeout=5)
