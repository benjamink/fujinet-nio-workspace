# Optional small Atari stream client

Status: implementation started; not a release or a replacement for the existing client.

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

## Work and acceptance

- [x] Prototype bounded, transport-independent exact-request replay with tests
  for lost read/write replies, partial writes, altered retries, would-block,
  stale/gapped sequences, capacity limits and sequence exhaustion.
- [ ] Finalize versioned wire contract, session token lifecycle, asynchronous
  open and reset/close semantics. The replay prototype is not a published API.
- [ ] Implement stream operations through existing routed network services;
  bound per-session RAM and describe memory costs.
- [ ] Add optional Atari SIO projection with fixed receive-length policy;
  measure padding vs an extra status exchange for realistic game packets.
- [ ] Matching Python builders/parsers, CLI and wire tests; console diagnostics.
- [ ] Library public block-pointer API, isolated archive members, polled 19200
  backend and client-owned storage. Document registers, ZP, IRQ/NMI and lifetime.
- [ ] Independent soft65c02 tests including byte/checksum errors, timeout,
  duplicate replay, partial progress, register restoration and buffer guards;
  report size and cycles. Full library `make check`.
- [ ] Experimental game build; do not remove the current NIO backend. Include
  lobby AppKey support without accidentally linking the old generic stack.
- [ ] Headless AltirraSDL tests through actual firmware and a local TCP peer:
  registration, game traffic, idle notification, retry injection, help disk,
  sound/DLI/VBI and logoff/reconnect. No public server traffic.
- [ ] Firmware doctests/Python tests, original game tests and comparative build
  sizes pass. Prepare clearly identified experimental firmware and ATR.
- [ ] User hardware feedback: startup from HSIO, fallback, help transitions,
  sound, DLIs/VBI, keyboard, reconnect and sustained gameplay. Emulator passes
  do not establish hardware timing correctness.

## Current evidence

`source scripts/env.sh && cmake --build repos/fujinet-nio/build/fujibus-pty-debug -j4`
then `repos/fujinet-nio/build/fujibus-pty-debug/tests/fujinet-nio-tests --test-case='stream*'`
passed six replay primitive cases. No new SIO or 6502 implementation exists yet;
soft65c02 and AltirraSDL validation of the experimental path remain outstanding.

The first primitive retains one exact request and result in fixed arrays. It
requires a separately validated session token and never silently wraps its
16-bit sequence. Session renewal without losing a live TCP connection must be
specified before this sequence policy is used in the wire implementation.
