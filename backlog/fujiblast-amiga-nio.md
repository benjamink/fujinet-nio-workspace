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
- [x] Decouple input/movement/render cadence from blocking NIO exchanges and
  demonstrate responsive held-key movement and bomb latency on stock A500.

Measurements, commands, limitations, and evidence directories are recorded in
`external/fujinet-fujiblast/docs/amiga-playing.md`. The 030 comparison shows
network waits dominate after rendering cost becomes small; do not call a
50 Hz emulator refresh measurement 50 game FPS.


### Implemented performance follow-up

The network worker, ordered/coalescing bounded queues, cached planar blitter
sprites/tiles, foreground scheduling, and late-frame pacing are implemented.
PAL stalled-NIO keyboard acceptance measured 65 foreground passes in 120
logical ticks, all 120 movement steps applied, no discarded steps, and an
100 ms maximum input-poll gap. Real Space input predicted the bomb during the
stall. The busy four-player case measured 15.6 FPS with 59.8 movement UPS in a
steady sample; do not claim 30/50 FPS for every scene.

Seven host test groups, PAL/NTSC live networking, PAL/NTSC held-key/stall tests,
screen captures, a pixel-by-pixel blitter oracle, and missing-broker cleanup
passed. One final NTSC run exceeded the input-gap target at 133 ms; the repeat
passed at 100 ms. The bound is not guaranteed across runs. Exact commands and evidence are in
`external/fujinet-fujiblast/docs/amiga-performance.md`.

Implementation and emulator acceptance are complete for this follow-up.
Retain the goal here pending the user's playability review. Physical hardware
is not represented by these emulator measurements.

### Scoreboard follow-up

- [x] Replace the Amiga's crowded 20-character HUD with 40 narrow glyphs:
  six-character names, separated scores, central timer, and seat colours.
  Keep the 320×200 bitmap and existing chip-RAM budget.
- [x] Select the four-player animated scene for visual verification with
  BOT1/BOT2/BOT3/PLAYER and distinct scores; retain the pixel-oracle check.

### Physical Amiga setup and audio follow-up (2026-11-20)

- [x] Inspect existing lobby server/name appkeys and compile-time fallback.
- [x] Add title-screen F1 setup for player name and server, validation,
  persistence, cancellation, and a route back after connection failure.
- [x] Retain the server when leaving a room; verify appkey boundaries and
  invalid inputs with host tests, plus real keyboard setup in Amiberry.
- [x] Port the actual background music and improve the basic sound substitutes.
  Work on this separately after server setup; the current audio is not a full port.

Setup implementation and evidence are documented in the game's
`docs/amiga-playing.md`. The physical binary remains `r2r/amiga/fujiblast-nio`.

### Joystick cornering follow-up (2026-11-20)

User reports passage-entry wobble and uses 38400 baud to avoid connection drops.
Reproduced a local diagonal-axis priority oscillation in the actual play-loop
selector. Amiga now retains the chosen turn priority until the stick changes,
with the existing blocked-turn fallback and unchanged collision rules.

- [x] Reproduce before fixing and cover all orientations/speeds, batched ticks,
  early/near-entry turns, walls/bombs, and cardinal alignment limits.
- [x] Build the physical executable; eight sanitizer host test groups pass.
- [ ] User confirms passage-entry improvement on the physical Amiga at 38400.

This input correction is not a serial-drop diagnosis or a claim that all possible
server position corrections have been eliminated.

The live emulator retest failed twice at NIO name persistence before gameplay
(evidence `20261120-112347-pal`, `20261120-112439-pal`). Keep that integration
failure open separately; no live-wire pass is claimed for this cornering fix.

Offline A500 scene 5 and its pixel oracle passed (`20261120-112521-pal`);
the dedicated host regression covers the actual corner-input sequence.

### Connection resilience and physical diagnostics (2026-11-20)

User reports frequent reconnect prompts at 38400 despite stable file transfers
and other apps at 57600. A single non-busy read failure previously dropped the
stream immediately; the protocol silence threshold is already 900 polls.

- [x] Add bounded read recovery using unchanged offset/size and NIO replay.
- [x] Retry only provably zero-progress write backpressure; never blindly replay
  uncertain writes with released library 0.2.0.
- [x] Back off empty reads and add bounded RAM logging in the normal binary:
  broker/native error details, retry/recovery/EOF/queue/idle reasons and counters.
- [x] Run focused failure-injection tests with sanitizers (nine groups).
- [x] Collect a physical-machine log to identify the remaining drop cause.

The new log identified the emulator's preceding persistence failure as broker
backend-open failure (cause 1). Explicitly preloading serial drivers did not
resolve it; that attempted launcher change was removed.
Detailed log instructions and recovery limitations are in `docs/amiga-playing.md`
in the game repository. Firmware, driver and library sources remain untouched.

The emulator backend-open failure was traced to memory exhaustion: the launcher
used `bogomem_size=1`, and the Amiberry log says "Unsupported bogomem size
262144". Historical purported 512+512 KB runs actually had only 512 KB chip RAM.
The launcher now requests `bogomem_size=2` (512 KB slow), and NIO appkeys initialize
the backend before graphics/audio allocation. Prior timing evidence is annotated
rather than represented as measurements of the corrected profile.

The logging/live test also exposed control messages sharing the worker's DOS
process port. Control RPCs now use their own worker-owned port, separating them
from Delay and file-I/O replies. This is a correctness fix required before using
the new diagnostics, not proof of the physical serial failure's root cause.

Final live acceptance with logging passed (`20261120-114522-pal`): persistence,
room list/join, movement/bomb, deliberate TCP cut and same-seat reconnect,
results, leave/reopen and shutdown. The diagnostic recorded the cut as `tcp-eof`;
no corrupt frames or queue overflows were reported. Nine host groups pass and
the production 68000 binary is rebuilt against released library 0.2.0.

The logging-enabled stalled-network run (`20261120-114638-pal`) retained the
connection, applied 120/120 movement ticks, predicted the keyboard bomb and
ran 73 foreground passes. It failed the strict input-gap assertion at 140 ms
(target 100 ms); do not record it as a full responsiveness pass.

### Physical serial request ownership regression (2026-11-20)

The fetched `fujiblast-net.log` reports `cause=7 serial=250` on the read of a
15-byte write acknowledgement, after about 49 seconds. This means native
`IOERR_UNITBUSY`, not a game silence threshold or a reported UART overrun.
User confirmed custom serial driver 0.11. The source failed to mark reused
requests pending to Exec; a deterministic real-driver guest regression fails
64/64 checks before the correction and passes afterward.

- [x] Correct BeginIO request state in the owning driver repository.
- [x] Handle stale reply-port wake-ups in the broker without false timeouts.
- [x] Pass Amiga native tests, guest request reuse checks and 100 warm exchanges.
- [x] Build identifiable serial 0.12 and broker 0.10 artifacts for physical use.
- [ ] User installs both devices, reboots, verifies loaded versions and retests
  physical gameplay at the existing baud. Preserve a fresh log if it drops.

Implementation and evidence: driver repository
`docs/amiga/serial-request-reuse-regression.md`. These are confirmed software
defects consistent with the physical error; physical resolution remains unproven.
No game, library API or firmware wire changes are required. Do not update the
workspace submodule pin until the driver fix is merged upstream.

Final guest evidence: WB3.2/030 `amiberry-20261120-120704` (19.80 s),
WB1.3/68000 `amiberry-20261120-120914` (99.68 s). Both include 64 request-state
checks and 100 measured warm exchange trials. The WB1.3 test's activity budget
was extended from the former one-trial budget to cover the longer test;
game and transport timeout settings are unchanged.

### NIO host history and Lobby/Custom setup

- [x] Add/select/delete up to five custom endpoints on the Amiga setup screen.
- [x] Store the list in one NIO AppStore value, separate from lobby appkeys.
- [x] Preserve the old selected host on first use, reject malformed history,
  deduplicate canonical endpoints, and retain errors for retry.
- [x] Add a Lobby/Custom selector with a separate build-time Lobby preset.
- [x] Pass sanitizer host tests and build using released library 0.2.0.
- [x] Resolve the public endpoint using the lobby registry supplied by the user:
  appkey 16 / FujiBlast advertises `fujinet.online:9910` with four rooms.
- [x] Finish live public-preset verification and rebuild the physical executable.
  WB1.3/030 evidence `20261120-130024-pal` shows five saved custom entries,
  wrapped addresses, save/reload, and the four live public rooms. Eleven host
  groups pass; the production 68000 artifact uses `fujinet.online:9910`.

Lobby is a bundled preset verified via `/viewFull`, not runtime HTTP discovery.
The DOS `ec.tnfs.io` host serves the lobby disk image. Custom history and the
public preset use the game's existing room-list flow. Implementation details
and controls are in the game's `docs/amiga-playing.md`.

### Amiga music and effects

- [x] Replace placeholder jingles/effects with the shared tune definitions.
- [x] Generate both gameplay voices from `music/play.txt` and enable round music.
- [x] Keep audio timing independent of rendering/network waits, with PAL/NTSC
  cadence, concurrent effects, mute/resume, and orderly device cleanup.
- [x] Verify sequencing on the host and audible playback in Amiberry; rebuild
  the physical 68000 executable and document evidence in the game repository.

Completed with twelve host groups, stock A500 WB1.3 audio acceptance
`20261120-132751-pal` (including captured PCM), and networked WB1.3/030
acceptance `20261120-132926-pal`. Detailed playback and lifecycle contracts
are in the game's `docs/amiga-playing.md`.
