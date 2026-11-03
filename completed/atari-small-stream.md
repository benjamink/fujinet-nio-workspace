# Optional small Atari stream client

Status: accepted as an optional version 1 path after emulator and user hardware
testing. Not a replacement for the general client or a published release.

## Accepted scope

Keep the working SYN-ACK WIRE NIO build and Q/W/P/R transport. Add an optional
small stream protocol, application-owned context/buffers and 6502 assembly API
(single context pointer in A/X). Firmware owns cursors and replay state and uses
existing routed network services. No socket access from the SIO carrier, no
platform conditionals in core services. Keep the U1MB workaround until the new
path is hardware-tested by Mark. No automatic release/push.

Measured baseline (library package 0.1.2): legacy XEX 12,718 bytes, NIO XEX
19,719 bytes. NIO library: 5,928 CODE, 1,220 BSS (1,024 packet buffers).
Target, not a promise: small network path about 2 KiB CODE, no hidden 1 KiB
packet workspace. Count lobby/AppKey support and runtime helpers in comparisons.

## Implementation and acceptance

- [x] Bounded exact-request replay; malformed retries, partial writes, NotReady,
  stale/gapped sequences, capacity checks and exhaustion tested.
- [x] Version 1 s/S/T projection, versioned capabilities, token and 32-bit
  sequence. Two exchanges per operation with bounded result padding.
- [x] Routed NetworkDevice/FileDevice session adapter. TCP cursors live in
  firmware. No new socket implementation, tasks or core platform conditionals.
- [x] Python payload builders/parsers, codec CLI, independent vectors/doctests.
- [x] Atari block-pointer ASM API, polled 19200 carrier, caller-owned 262-byte
  context. 875 code bytes, 17 scratch BSS bytes and 4 private ZP bytes.
- [x] soft65c02 transaction/guard/retry tests and active-low POKEY regression;
  complete all-target library `make check` passes.
- [x] Dedicated nio-apps STREAMTEST boot disk with fragmented echo server,
  immediate-VBI sound, colour-band DLIs, keyboard toggles and results display.
- [x] Headless AltirraSDL diagnostic: 126 echoes spanning all 120 block sizes,
  zero mismatches, VBI progression, D/S toggles and clean close.
- [x] Optional game backend. Existing backend unchanged. Headless
  real-firmware/local-server lobby AppKey, join, seat choice, disk help, logoff
  and rejoin passed. Original host and 28-check soft65c02 game tests passed.
- [x] Firmware CTest (four tests), Python tests and configured Atari ESP32 build.
- [x] User hardware testing: stock speed and U1MB HSIO startup/fallback, help
  transitions, sound, DLI/VBI, keyboard and sustained traffic. Do not remove the
  established workaround from the standard backend before this acceptance.

## Scope/limitations of version 1

The small-stream library only supports one TCP stream per ingress, up to 120
bytes per call, plus the title's creator=1/app=1 AppKey lookup. No HTTP/TLS,
zero-length half-close or multi-client sharing. Reply padding trades bandwidth
for simple framing; the candidate does not claim optimal wire utilization.
Tokens/replay do not survive firmware restart. Sequence is 32-bit and stops on
exhaustion rather than wrapping. Socket open/progress uses the existing backend;
DNS scheduling is not redesigned. The Python CLI is a codec, not a new SIO host.

Game XEX: 13,941 bytes versus 19,719 existing NIO and 12,718 legacy. The 5,778
byte saving is measured; hardware acceptance is limited to the recorded workloads and setup.

Durable implementation docs:
- repos/fujinet-nio/docs/atari/small-stream.md
- repos/fujinet-nio-lib/docs/atari-small-stream.md
- repos/nio-apps/docs/atari-small-stream.md

Verification commands (source scripts/env.sh first):
- make -C repos/fujinet-nio-lib check
- ctest --test-dir repos/fujinet-nio/build/fujibus-pty-debug --output-on-failure
- repos/fujinet-nio/scripts/run-python-tests (from its owning repository)
- ./build.sh -b (from repos/fujinet-nio, Atari v1 16MB profile)
- make -C repos/nio-apps atari-stream-disk
- python3 integration-tests/atari-sio/run_stream_test.py --output <new directory>
- python3 integration-tests/atari-sio/run_syn_ack_wire.py --checkout repos/syn-ack-wire --allow-dirty --stream --output <new directory>

Hardware package: `scratch/atari-small-stream-20261103/` (primary disk
`streamtest.atr`, matching ESP32 firmware, instructions, source revisions and
SHA256 checksums). Final diagnostic run: 126 echoes, zero errors, 3474 VBI frames.

## User hardware acceptance

Firewall corrected; STREAMTEST completed 459 echoes at stock speed and 600
starting with U1MB HSIO, with DLI and sound on and zero errors. User subsequently
reported SYN-ACK WIRE gameplay, help, sound, DLI/colours and logoff/rejoin working.
The stale game/missing-grid observation is deferred for separate diagnosis; it
has no established cause and is not silently declared fixed by this acceptance.

Production integration contract now documents audience, measured client memory,
firmware allocation, register/interrupt ownership, synchronous latency, bandwidth,
partial transfers, exact retry obligations, restart limits and wire compatibility.
No general backend removal or new published release is part of this acceptance.

Production follow-up verification: complete library `make check`, firmware CTest,
headless STREAMTEST normal run and refused-peer regression (displayed error count).

Accepted 2026-11-03. Final follow-up tests: 126 echoes, zero errors; refused-peer
case shows status 5 and Errors 1; firmware CTest 4/4; complete library check and
all 28 existing game soft65c02 checks pass. Implementation is on the owning NIO
repositories' master branches; game integration is on `nio-small-stream` in
markjfisher/syn-ack-wire, separate from the sound-restoration PR. No release tag
or binary GitHub release was created. The general game backend remains default.
