# FujiBlast Amiga NIO port

Status: IN PROGRESS — implementation and verification complete; awaiting user review.

## Goal

Port `external/fujinet-fujiblast` to Amiga using FujiNet NIO and the
**released fujinet-nio-lib 0.2.0**, following the author's supplied visual
reference. Work on the game's `amiga-nio` branch (already created).

Follow this checklist directly. No BMAD workflow, generated specs, review
loops, or approval checkpoints are required. Record progress and verification
here; keep detailed implementation documentation in the game repository.

## Scope and working assumptions

- Preserve shared gameplay and the existing server protocol. The Amiga port
  must not depend on legacy fujinet-firmware or fujinet-lib.
- Download and cache the published library, following FujiBlast's existing
  `_cache` convention. Do not depend on the workspace library checkout.
- Use `repos/syn-ack-wire/client/` as a read-only Amiga integration reference.
- Working hardware baseline: 68000, OCS/ECS, Kickstart/Workbench 1.3+, up to
  1 MB total RAM, PAL and NTSC. These are implementation assumptions, not
  additional user requirements; validate resource use during development.
- Adapt the existing VGA assets to a 320×200, 32-colour planar display.
  Preserve the reference's shaded art, four player colours, title, room,
  arena, and results layouts; exact VGA colours are not an OCS requirement.
- Leave unrelated changes and submodule pins alone. Commit completed work
  with its verification; never push.

## Dependencies and findings

- [NIO 0.2.0 release](https://github.com/fujinet-nio/fujinet-nio-lib/releases/tag/v0.2.0):
  use `fujinet-nio-lib-amiga-0.2.0.zip`, containing
  `fujinet-nio-amiga.a` and headers. The `amiga-driver` variant is for resident
  drivers, not this application.
- Expected ZIP SHA256:
  `cf5c579bcc185d258bb2bbd26cbfef4b2d48a0f20eb5cd9ee298dd17c9413f6c`.
- The resident `fujinet-nio.device` broker must be loaded before game startup.
  Released `fn_legacy_appkey.h` compatibility functions use NIO FileDevice;
  their name does not imply legacy firmware support.
- Existing VGA artwork and conversion helpers closely match the reference.
  Existing offline scenes 1–5 and input hooks can support guest validation.
- Source workspace `scripts/env.sh` before builds/tests. Follow
  [test policy](../docs/agent-test-policy.md) and
  [Amiberry procedure](../docs/amiga/amiberry-testing.md).

## Ordered work

- [x] Inspect platform interfaces, artwork, library acquisition, networking,
  and the SynAckWire Amiga reference.
- [x] Create `amiga-nio` in the FujiBlast repository.
- [x] Verify the release ZIP checksum and cross-link an actual release
  `fn_init()` program. Compiler/NDK readable; `-m68000 -mcrt=nix13` passed.
- [x] Add `make amiga`: fetch the pinned release, verify/cache it, isolate
  Amiga objects/assets, and produce `r2r/amiga/fujiblast-nio`.
- [x] Reuse the existing indexed artwork with transparency, animation frames and
  distinguishable player colours; convert dirty display regions to OCS planes.
- [x] Implement Amiga OS startup/cleanup, display, keyboard/joystick input,
  PAL/NTSC timing, effects/jingles and mute. Preserve the platform's
  60-logical-ticks-per-second contract and use dirty rendering.
- [x] Implement NIO TCP transport under the existing platform interface:
  bounded COBS/Fletcher framing, stream offsets, encoded-byte credits,
  idle polling, EOF draining and reconnect cleanup.
- [x] Integrate NIO appkeys before the first read. Fix bounded room URL
  serialization and port validation; do not truncate a persisted endpoint.
- [x] Add and run focused host tests for the edge cases below.
- [x] Run bounded guest scenes and live server/bot acceptance through actual
  NIO; retain screenshots/logs and clean up only test-owned processes/images.
- [x] Document build, broker setup, server configuration, controls, CLI stack,
  hardware requirements and verified limitations in the game repository.
- [x] Commit verified implementation locally and record commands/results here.

## Required behavior and checks

- Empty cache downloads once; populated cache supports offline rebuilds.
  Corrupt or incomplete archives fail clearly.
- Missing broker or partial OS initialization reports failure and releases
  resources. Busy audio permits silent play.
- Split/coalesced frames, malformed checksums and oversized frames recover
  correctly. NOT_READY is not a disconnect; consume buffered data before EOF.
- Partial writes advance by accepted bytes without duplicating prefixes.
  Reopen resets stream offsets and framing. Preserve byte-credit wraparound,
  the server's 192-byte window and common 48-byte credit threshold.
- Missing appkeys retain defaults; long endpoints cannot overflow storage;
  invalid ports cannot wrap. Name/room persistence survives restarting.
- Held movement, fire edges, text entry, PAL/NTSC timing and mute work.
  Four-player overlap and blasts restore backgrounds without trails.
- Title, room, arena and results remain readable and recognizable against
  the supplied reference. Leaving and quitting release resources.

## Verification

All listed targets/scripts are implemented. Run from
`external/fujinet-fujiblast` after sourcing the workspace environment:

- `make test-amiga`: mocked NIO transport/appkeys, download/cache behavior,
  planar conversion, input and timing tests.
- `make amiga`: published-library cross-build, then offline cached rebuild.
- `python3 tools/amiga/accept.py --scenes --standard pal` and
  `python3 tools/amiga/accept.py --scenes --standard ntsc`: title and scenes
  1–5, screenshot inspection and bounded teardown.
- `python3 tools/amiga/accept.py --live`: isolated server/bots through POSIX
  NIO and Amiberry; name persistence, list/join, movement/bombs,
  disconnect/reconnect, results, leave and quit.

Also passed: `python3 tools/amiga/accept.py --missing-broker` and the final
NTSC busy-scene check (`--scenes --standard ntsc --scene 5`). Emulator results do not establish physical serial timing
or audible quality. If library code must change, full `make check` is required;
no library or firmware changes are currently expected.

## Exit criteria

- [x] A fresh checkout builds with the published NIO 0.2.0 dependency and
  rebuilds using its cache.
- [x] Amiga gameplay, persistence, reconnect and cleanup pass host and live
  guest checks; visual evidence covers PAL/NTSC and all main screens.
- [x] Verification results and remaining hardware limitations are documented.
- [ ] User accepts the port; move this record to `completed/`.

## Current evidence

Implemented and committed in the game repository on `amiga-nio`:
`2807355c88af9a2852226849a028b152a7780889`.

- `make test-amiga`: all five host test groups passed, including sanitizer
  runs of transport, appkeys, controls and the production movement code.
- `make amiga`: passed with the published 0.2.0 archive. Forced cached rebuild
  passed with unusable HTTP(S) proxies; cache tests prohibit network calls.
- Amiberry: OCS A500/68000, 512 KB chip + 512 KB slow RAM, OS1.3.
  PAL and NTSC scenes passed, including real Escape key input. Final live
  acceptance passed persistence, room listing, movement, bomb placement,
  external TCP cut, same-seat recovery, results and leave. Missing-broker
  startup returned an error and exited cleanly.
- [Game documentation and exact retained evidence runs](../external/fujinet-fujiblast/docs/amiga.md).
- [Preview assembled from actual PAL guest display captures](../external/fujinet-fujiblast/docs/amiga-preview.png).
- Built executable: `external/fujinet-fujiblast/r2r/amiga/fujiblast-nio`.
- No firmware, driver or library source changes. Physical serial timing and
  audible quality remain hardware checks, not claimed emulator results.

No changes were pushed. The implementation is ready for user review; retain
this record in `backlog/` until acceptance, then move it to `completed/`.

## User review: performance follow-up (2026-11-19)

User reports unplayably sluggish keyboard movement on stock A500. Functional
acceptance is insufficient for playability; stock A500 acceptance remains open.

- [x] Add opt-in game FPS, movement UPS, render and blocking-I/O timings.
- [x] Add a selectable accelerated 68030 profile and `run.sh` launcher alias.
- [x] Remove per-pixel software division in the Amiga renderer; rerun live
  movement/bomb/reconnect/results acceptance and host tests.
- [ ] Decouple input/movement/render cadence from blocking NIO exchanges and
  demonstrate responsive held-key movement and bomb latency on stock A500.

Measurements, commands, limitations, and evidence directories are recorded in
`external/fujinet-fujiblast/docs/amiga-playing.md`. The 030 comparison shows
network waits dominate after rendering cost becomes small; do not call a
50 Hz emulator refresh measurement 50 game FPS.
