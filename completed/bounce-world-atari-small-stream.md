# Bounce World Atari small-stream acceptance

Status: accepted for normal Atari use after user hardware testing; production cleanup complete.

- [x] Opt-in Atari TCP adapter; default packet backend and AppStore retained.
- [x] Separate executable/object/ATR outputs; no U1MB/HSIO configuration changes.
- [x] 120-byte read-ahead with bounded frame delivery, partial writes, failure latch and prefix drain.
- [x] Host regression suite, soft65c02 stream/keyboard tests, Atari and Linux builds.
- [x] Sequential headless Altirra/real NetSIO firmware runs: packet and stream,
  fragmented 4/80-object responses, client list drain, input, quit and rejoin.
- [x] Actual server-3.0.0.jar: moving object, input, quit and re-registration.
- [x] Size/rate comparison and limitations in owning repository docs/atari-small-stream.md.
- [x] User hardware acceptance: sustained normal small-world animation, colour,
  sound and input; no major recurring pauses after firmware capture fixes.
  Dense-world and all-expansion coverage remain limits, not claimed hardware passes.
  Packet backend remains available.

Candidate: scratch/bounce-world-small-stream-readahead-20261103/bwcn-stream.atr;
comparison disk bwcn-packet.atr and evidence/checksums alongside it.
Historical candidate above predates capture fixes. Production use requires current
Atari firmware (capture fixes through ffaf8954); upload with ./build.sh -u.
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

Historical hardware choppiness investigation (now closed): separate `disk-atari-stream-diag` variant
shows rate, last/max fetch, wire write/read time, Busy/NotReady count, read calls
and live phase on row zero. Candidate:
`scratch/bounce-world-stream-diagnostic-20261103/bwcn-stream-diag.atr`.
No new IRQ/NMI instrumentation; normal stream disk remains uninstrumented.
Host accounting/clock-wrap tests and headless normal/injected-400ms traffic pass;
This was followed by user row captures and firmware fixes. Do not attribute
hardware stalls to the server or SIO until the observations distinguish them.


Production cleanup (2026-11-03):
- Removed the temporary timing overlay, hooks, diagnostic build and its tests.
- Normal disk: repos/bounce-world-client-nio/disk-images/atari-stream/bwcn.atr.
- Retained firmware recovery tests and flight recording; consolidated durable
  contract in repos/fujinet-nio/docs/atari/sio-capture.md.
- Hardware evidence: scratch/min-001 through min-014; user accepted final build
  after sustained running. PC sleep/network outages and console printing can
  still interrupt application updates; those are not promises of uninterrupted IO.
- Verified host tests, 11 soft65c02 keyboard checks, Atari stream/packet and Linux
  builds; headless stream/packet integration checks cover fragmented 4/80-object
  worlds, input, quit and rejoin. Screenshots confirm the timing row is absent.
- Firmware CTest 4/4 and Atari v1 16MB ESP32 build passed.
- No library API or protocol changes in cleanup. No release, push or workspace
  submodule pin change; repository commits remain local pending publication.
