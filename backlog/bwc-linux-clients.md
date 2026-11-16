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
