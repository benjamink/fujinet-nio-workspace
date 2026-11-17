# Bouncy World Linux clients

Fix and polish the existing terminal client first, then add a separate graphical
Linux client. Owner: `repos/bounce-world-client-nio`.

- [x] Fix Info persistence; batch terminal frames and restore terminal state.
- [x] Verify repeated Info toggles, frame clearing, and PTY cleanup; commit text fixes.
- [x] Add `make linux-gfx` / `build/bwcn.linux-gfx`, leaving `linux` independent of SDL.
- [x] Add an SDL window with editable destination/pilot settings, an animated shape
  gallery, colorful pixel graphics, persistent controls, client list and broadcasts.
- [x] Keep input/rendering responsive during network waits. One worker owns NIO;
  publish synchronized snapshots and serialize commands. Reuse the existing CSV,
  coordinate decoder, body-ID interpolation math and app-store settings.
- [x] Test framing, delayed/empty/malformed snapshots, interpolation, UI events,
  clipping, resize and cleanup. Run existing host tests and both Linux builds.
- [x] Document controls, dependencies, shape limitations and verification; commit.

Use Atari's setup/presentation and Amiga's intermediate rendering as references.
Do not change canonical shape definitions: Amiga has unfinished hand-authored
outlines, and the fallback tracer treats every non-space cell as fully occupied.
Expose outline/block views and a gallery so those limitations remain inspectable.
No server or library implementation changes are expected. Do not push or move
workspace submodule pins to unmerged commits.

Before checks, source `$NIO_WORKSPACE/scripts/env.sh`. Use focused native tests and
SDL dummy-video checks, then a graphical smoke test. Distinguish fixture coverage
from live NIO testing. Record results here when complete.

## Implementation results — 2026-11-16

Implementation is complete. The BMad draft was removed; no BMad cycle was used.
The client repository contains two local commits (not pushed):

- `44b8c3f5`: terminal Info persistence, differential frame output and cleanup.
- `218c9144`: separate SDL graphical client and its documentation/tests.

Passed after sourcing the workspace environment:

- `make linux test-linux-text`
- `make linux-gfx test-linux-gfx test-linux-network`
- `make test-host`
- Graphical/worker tests with AddressSanitizer and UndefinedBehaviorSanitizer.
- Dummy-video screenshots of setup, world and gallery; actual desktop offline
  window smoke run (30 frames, automatic exit).

The network worker tests exercise the actual worker with a fake NIO boundary,
including fragmented replies, status commands, command ordering, cancellation,
reconnect after malformed input, and 255-record snapshots. No live server session
was used. Build/run instructions, controls and shape limitations are in
`repos/bounce-world-client-nio/docs/linux-clients.md`.

## Remaining acceptance

- [ ] Try the clients against the user's live FujiNet/Bouncy World setup and
  confirm the presentation and controls. Move this record to `completed/` after
  that acceptance. Implementation and automated verification above are finished.

Workspace submodule pins were not changed: the implementation commits have not
been merged upstream. The pre-existing firmware changes were left untouched.


## Pico soak investigation — 2026-11-17

The live linux-gfx capture completed 695 replies for 696 writes, then hit the
client's five-second reply deadline while NIO reads returned NOT_READY. It recorded
no NIO timeout, malformed frame or EOF. Some earlier replies took over one second.
This is evidence of missing/delayed data, not yet proof of a Pico defect.

- [x] Add bounded Pico raw-TCP diagnostics without enabling FN_DEBUG, preserving
  the SD-testing branch. Track accepted/acknowledged/received/consumed bytes,
  output/callback errors, queue/window/retransmission state and close evidence.
- [ ] Capture a failing live soak with the diagnostic firmware and linux-gfx
  stderr; identify where progress stops and fix the demonstrated cause.
- [ ] Consider shared-client stale-snapshot recovery after the baseline capture.
  Do not blindly resend on the same TCP stream: replies have no request ID.
  Safe options require draining the outstanding framed reply before another
  request, or reconnecting and registering again. Count soft deadlines and
  recovery attempts separately so recovery cannot conceal soak failures.

Firmware implementation and capture-field documentation belong in
`repos/fujinet-nio/pico2w/README.md`. No library or protocol change is required
for this instrumentation. Hardware root-cause verification remains pending.

Instrumentation committed locally as firmware commit `3764fe0c` on `pico/sd-spi`.
Verification: all seven native Pico CTest checks pass, including silent normal
traffic, stall/recovery, deferred reset/output errors, callback detachment,
bounded close queue and global output rate limiting. The Pico 2 W UF2 built with
`FN_DEBUG=OFF`; the old build cache's removed ISRG certificate path was reset to
the current default Mozilla bundle. Artifact:
`/tmp/nio-pico2w-build/fujinet_nio_pico2w.uf2`. Not flashed or hardware-tested.
Workspace documentation checked with `git diff --check`; no submodule pin moved.

### First diagnostic soak evidence

The 2026-11-17 run failed after approximately 36 minutes with a host-side
fn_write transport timeout, not the prior application reply deadline. Packet
capture and Pico counters agree that the last successful request/reply completed;
the next six bytes never entered the instrumented raw TCP send path. Server EOF
followed its 30-second idle timeout. Root cause remains open; next observation
should cover host/Pico USB, framing and dispatch. Detailed frame evidence:
`repos/fujinet-nio/pico2w/bounce-soak-2026-11-17.md`.

### USB evidence and Linux mitigation

Filtered USB capture shows the failed Write stopped after sixteen one-byte
submissions (header only); the six-byte body and closing delimiter were never
submitted. A pending header transfer completed when Close began one second
later. This narrows the failure to incomplete host-side serial submission,
without proving why USB completion/readiness was delayed.

The Linux library now uses its existing complete-frame bulk-write callback,
handles partial writes without replay, and bounds interrupted/backpressured
writes with a monotonic deadline and periodic readiness rechecks. Both Linux
clients were rebuilt; no firmware reflash or application timeout change.
Library make test and client text/network/gfx checks passed. Full make check
was attempted: main targets and amiga-driver built, but mac68k is blocked by
missing Retro68 m68k-apple-macos-gcc. It is not an all-target pass.

- [ ] Repeat hardware soak with the rebuilt Linux client; verify complete
  frame submissions and investigate any remaining failure before claiming a fix.

### Authored vector shapes

User superseded the earlier instruction to leave Amiga outlines unchanged:
both Amiga and Linux now render all 19 fixed original shapes from one authored
vector table, including distinct single-cell symbols. The example Amiga
overrides and runtime cell-tracing render path were replaced. Linux SDL tests,
host vectors/bounds tests, both Amiga builds and Linux gallery inspection pass.
Amiga live presentation and user gallery acceptance remain pending.
