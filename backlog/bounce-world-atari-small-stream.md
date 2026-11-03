# Bounce World Atari small-stream acceptance

Status: implementation and automated validation complete; user hardware trial pending.

- [x] Opt-in Atari TCP adapter; default packet backend and AppStore retained.
- [x] Separate executable/object/ATR outputs; no U1MB/HSIO configuration changes.
- [x] 120-byte read-ahead with bounded frame delivery, partial writes, failure latch and prefix drain.
- [x] Host regression suite, soft65c02 stream/keyboard tests, Atari and Linux builds.
- [x] Sequential headless Altirra/real NetSIO firmware runs: packet and stream,
  fragmented 4/80-object responses, client list drain, input, quit and rejoin.
- [x] Actual server-3.0.0.jar: moving object, input, quit and re-registration.
- [x] Size/rate comparison and limitations in owning repository docs/atari-small-stream.md.
- [ ] Hardware acceptance: user tests disk with U1MB/HSIO, colour/sound, short key
  presses, dense world and quit/rejoin. Keep packet backend available.

Candidate: scratch/bounce-world-small-stream-readahead-20261103/bwcn-stream.atr;
comparison disk bwcn-packet.atr and evidence/checksums alongside it.
Use the previously installed small-stream firmware; no firmware changes needed.
No new release or push was performed. Repository implementation is committed
locally; workspace submodule pin remains unchanged pending publication.

Measurements: XEX 28,938 -> 26,285 bytes; BSS 2,765 -> 3,089; allocation end
$93CA -> $8AB1. Deterministic peer fetches/s packet vs stream: 4 objects
8.08 vs 8.83, 80 objects 5.17 vs 3.47. Emulator observations, not hardware UPS.

Commands (source scripts/env.sh first):
- make -C repos/bounce-world-client-nio disk-atari disk-atari-stream linux
- make -C repos/bounce-world-client-nio test-host test-atari-keyboard
- make -C repos/fujinet-nio-lib test-atari-stream
- python3 integration-tests/atari-sio/run_bounce_stream.py --backend stream --output <new directory>
- python3 integration-tests/atari-sio/run_bounce_stream.py --backend packet --output <new directory>
- python3 integration-tests/atari-sio/run_bounce_stream.py --server 127.0.0.1:9003 --output <new directory>

Run emulator tests sequentially (shared NetSIO port). The locally started Java
server was stopped after testing; no user-owned server was stopped.

Read-ahead follow-up: request 120 when empty, retain excess across frame boundaries
and writes, defer EOF until drained, reset on init/open/close. Host tests prove a
35-byte world update uses one wire read; full host/keyboard tests and headless
4/80-object, quit/rejoin checks pass. Additional cost versus initial stream:
270 executable bytes and 123 BSS bytes. No new library/firmware changes.
