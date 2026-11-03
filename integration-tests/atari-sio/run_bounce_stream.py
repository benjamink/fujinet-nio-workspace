#!/usr/bin/env python3
"""Real firmware/headless Atari BW framing, keyboard and comparative fetch rates.
Uses an isolated deterministic TCP protocol peer, never a public game server.
"""
import argparse
import json
import os
from pathlib import Path
import socketserver
import struct
import sys
import threading
import time

root = Path(os.environ['NIO_WORKSPACE'])
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--response-delay-ms', type=int, default=0, help='Delay x-w replies to exercise network backpressure')
p.add_argument('--backend', choices=('stream', 'packet'), default='stream')
p.add_argument('--output', type=Path, required=True)
p.add_argument('--server', help='Use an already running real server, host:port, with moving objects')
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(root/'repos/nio-config/scripts'))
from atari_shot_netsio import boot
from atari_ui import read_os_screen, symbols
repo = root/'repos/bounce-world-client-nio'
variant = 'atari-' + a.backend if a.backend != 'packet' else 'atari'
build = repo/'build'/variant if a.backend != 'packet' else repo/'build'
labels = symbols(build/'bwcn.atari.lbl')
state = dict(count=4, registrations=0, closed=0, samples=[], commands=[], failures=[])

class Peer(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(120)
        try:
            while line := self.rfile.readline():
                cmd = line.decode('ascii').strip()
                state['commands'].append(cmd)
                op = cmd.split()[0]
                if op == 'x-add-client':
                    state['registrations'] += 1
                    payload = b'\x01'
                elif op == 'x-ws':
                    payload = struct.pack('<HHH8B',40,24,state['count'],1,1,1,1,1,1,0,0)
                elif op == 'x-who':
                    payload = b'player  '*30  # exercise prefix + drain (>160)
                elif op == 'x-w':
                    if a.response_delay_ms: time.sleep(a.response_delay_ms/1000)
                    n = state['count']
                    state['samples'].append((time.monotonic(),n))
                    step = len(state['samples']) % 255 + 1
                    payload = bytes([step,0,n]) + b''.join(bytes([0,(i*3+step)%35,(i*2)%19]) for i in range(n))
                elif op == 'close':
                    state['closed'] += 1
                    break
                else:
                    raise AssertionError(f'unexpected command {cmd!r}')
                frame = struct.pack('<H', len(payload)+2) + payload
                # Split header and records deliberately; repeat identically for both backends.
                for start, end in [(0,1),(1,7),(7,119),(119,len(frame))]:
                    part = frame[start:min(end,len(frame))]
                    if part:
                        self.wfile.write(part);self.wfile.flush();time.sleep(.002)
        except Exception as exc:
            state['failures'].append(repr(exc))

class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True

with Server(('127.0.0.1',0), Peer) as server:
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    def inspect(view):
        def rows(): return read_os_screen(view.bridge)
        def wait(check, timeout=90):
            until=time.monotonic()+timeout
            while time.monotonic()<until:
                if check():return
                if state['failures']:raise AssertionError(state['failures'])
                time.sleep(.1)
            view.screenshot(a.output/'failure.png')
            raise AssertionError('\n'.join(rows())+'\n'+repr(state['commands'][-10:]))
        wait(lambda:any('press S to enter' in row for row in rows()))
        view.key('S');view.type(a.server or f'127.0.0.1:{server.server_address[1]}');view.key('RETURN')
        time.sleep(.5)
        view.key('N');view.type('stream');view.key('RETURN');time.sleep(.5);view.key('RETURN')
        wait(lambda:any('launch world' in row for row in rows()))
        view.key('SPACE')
        if a.server:
            wait(lambda:view.bridge.peek(labels['_is_running_sim'],1)[0]==1)
            seen=set()
            def advancing():
                seen.add(view.bridge.peek(labels['_current_step'],1)[0])
                return len(seen)>=12
            wait(advancing)
            assert view.bridge.peek(labels['_err'],1)[0]==0
            view.screenshot(a.output/'real-world.png')
            before=view.bridge.peek(labels['_is_showing_info'],1)[0]
            view.key('I');wait(lambda:view.bridge.peek(labels['_is_showing_info'],1)[0]!=before,10)
            view.key('Q');wait(lambda:any(a.server in row for row in rows()))
            view.key('RETURN');wait(lambda:any('launch world' in row for row in rows()))
            view.key('SPACE');seen.clear();wait(advancing)
            assert view.bridge.peek(labels['_err'],1)[0]==0
            view.key('Q');wait(lambda:any(a.server in row for row in rows()))
            (a.output/'result.json').write_text(json.dumps({'real_server':a.server,'distinct_steps':len(seen),'rejoined':True})+'\n')
            return
        report={}
        for count in (4,80):
            state['count']=count
            begin=len(state['samples'])
            wait(lambda:len(state['samples'])>=begin+25)
            samples=[t for t,n in state['samples'][begin+3:] if n==count]
            report[str(count)]={'fetches_per_second':(len(samples)-1)/(samples[-1]-samples[0]),'samples':len(samples)}
            assert view.bridge.peek(labels['_is_running_sim'],1)[0] == 1
            view.screenshot(a.output/f'objects-{count}.png')
        before=view.bridge.peek(labels['_is_showing_info'],1)[0]
        view.key('I');wait(lambda:view.bridge.peek(labels['_is_showing_info'],1)[0]!=before,10)
        view.key('Q');wait(lambda:state['closed']==1)
        wait(lambda:any('127.0.0.1:' in row for row in rows()))
        view.key('RETURN');wait(lambda:state['registrations']==2)
        wait(lambda:any('launch world' in row for row in rows()))
        view.key('SPACE');n=len(state['samples']);wait(lambda:len(state['samples'])>=n+5)
        view.key('Q');wait(lambda:state['closed']==2)
        assert not state['failures'],state['failures']
        report['registrations']=state['registrations'];report['clean_closes']=state['closed']
        (a.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))
    try:
        boot(repo/f'disk-images/{variant}/bwcn.atr',inspect,out=a.output/'boot')
    finally:
        server.shutdown()
        (a.output/'peer.json').write_text(json.dumps(state,indent=2)+'\n')
