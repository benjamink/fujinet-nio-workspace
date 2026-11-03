#!/usr/bin/env python3
"""Headless boot of STREAMTEST against real NIO firmware and a fragmented echo peer."""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

root = Path(os.environ['NIO_WORKSPACE'])
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--refuse-connection', action='store_true',
               help='Verify the displayed error count when the TCP peer is unavailable')
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(root/'repos/nio-config/scripts'))
from atari_shot_netsio import boot
from atari_ui import read_os_screen, symbols
labels = symbols(root/'repos/nio-apps/build/atari/bin/streamtest.lbl')
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
with (a.output/'echo.log').open('w') as log:
    server = subprocess.Popen([sys.executable, '-u', str(root/'repos/nio-apps/tools/stream_echo.py'),
                               '--port', str(port)], stdout=log, stderr=subprocess.STDOUT)
    try:
        time.sleep(.5)
        assert server.poll() is None
        if a.refuse_connection:
            server.terminate()
            server.wait(timeout=5)
        def inspect(view):
            def wait(check, timeout=90):
                until = time.monotonic()+timeout
                while time.monotonic()<until:
                    if check(): return
                    time.sleep(.2)
                raise AssertionError('\n'.join(read_os_screen(view.bridge)))
            wait(lambda: any('Echo server URL' in row for row in read_os_screen(view.bridge)))
            view.type(f'tcp://127.0.0.1:{port}')
            view.key('RETURN')
            if a.refuse_connection:
                wait(lambda: any('Stopped: error 5' in row for row in read_os_screen(view.bridge)))
                assert view.bridge.peek16(labels['_stream_passes']) == 0
                assert view.bridge.peek16(labels['_stream_errors']) == 1
                assert any('Errors     1' in row for row in read_os_screen(view.bridge))
                view.screenshot(a.output/'refused.png')
                (a.output/'result.txt').write_text('Refused TCP peer: status 5, zero echoes, displayed errors 1\n')
                return
            count = lambda: view.bridge.peek16(labels['_stream_passes'])
            errors = lambda: view.bridge.peek16(labels['_stream_errors'])
            wait(lambda: count()>=20)
            assert errors()==0
            f0=view.bridge.peek16(labels['_stream_frames'])
            for key,label in [('D','_stream_dli'),('S','_stream_sound')]:
                view.key(key)
                wait(lambda: view.bridge.peek(labels[label],1)[0]==0, 10)
            n=count();wait(lambda: count()>=n+10)
            assert view.bridge.peek16(labels['_stream_frames']) != f0
            for key,label in [('D','_stream_dli'),('S','_stream_sound')]:
                view.key(key)
                wait(lambda: view.bridge.peek(labels[label],1)[0]==1, 10)
            n=count();wait(lambda: count()>=max(n+10,125))
            assert errors()==0
            view.screenshot(a.output/'running.png')
            report=f'Echoes={count()} errors={errors()} frames={view.bridge.peek16(labels["_stream_frames"])}\n'
            (a.output/'result.txt').write_text(report)
            view.key('Q')
            wait(lambda: any('Reset to run again' in row for row in read_os_screen(view.bridge)), 10)
            print(report)
        boot(root/'repos/nio-apps/build/atari/streamtest.atr', inspect, out=a.output/'boot')
    finally:
        server.terminate()
        server.wait(timeout=5)
