---
id: SPEC-palm-hotsync
companions:
  - brownfield.md
  - palm-protocols.md
  - cradle-sharing.md
  - failure-modes.md
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Palm OS support in FujiNet NIO

## Why

A vision to realize, with prior art. Classic fujinet-firmware gained Palm support on the FN-RS232 board (dillera, branch `palm-demo-fozz`):

- a HotSync server, so a Palm in a serial cradle, or on Wi-Fi via NetSync, can install apps, back up and receive a calendar;
- Palm OS apps that reach the network through FujiBus over the same cradle.

That work stalled upstream (FujiNetWIFI PR #1826) on how HotSync may share the bus port. NIO is a clean re-interpretation of the firmware. Its channel/transport split gives the line-sharing problem a natural home, and its POSIX build and tests make the protocol work testable off-device. The classic code is reference material only. Everything is re-implemented to NIO's architecture and standards.

## Capabilities

- **CAP-1**
  - **intent:** NIO contains a portable Palm HotSync protocol core (SLP, PADP with CMP, NetSync, DLP, PDB/PRC files, and the sync session), independent of any device, bus or platform.
  - **success:** doctest suites replay the recorded Palm OS 3.3 serial captures and the palm-sync NetSync recording and pass on the POSIX presets. The same sources compile in an ESP32 build.

- **CAP-2**
  - **intent:** A Palm can HotSync with NIO over the network (NetSync, TCP 14238). The sync identifies or names the user, installs queued `.prc`/`.pdb` files, and backs up databases.
  - **success:** against a POSIX NIO build, `fake_palm.py` (or a successor) completes a sync. A queued file moves from `install/` to `installed/`, and the backup appears under `backup/<user>/`. The same flow is shown on an FN-RS232 ESP32 board against a real Palm's Network HotSync.

- **CAP-3**
  - **intent:** Palm OS apps talk to NIO through `fujinet-nio-lib`, using NIO's own devices and commands over the cradle serial port.
  - **success:** FN Test, rebuilt on the new lib platform, gets FujiNet info and fetches a URL through NetworkDevice from a real Palm (OS 3.3) on an FN-RS232 board running NIO, and from CloudpilotEmu against POSIX NIO.

- **CAP-4**
  - **intent:** One serial cradle serves both FujiBus app traffic and HotSync button-press syncs, without HotSync code touching the UART.
  - **success:**
    - With the cradle on the RS-232 port, pressing the HotSync button completes a sync.
    - An app session started afterwards works without reconfiguration.
    - Unit tests cover the hand-off state machine: app activity holding the line, stray-byte early release, a WAKEUP inside a window, a WAKEUP arriving late in a window, and baud restore.

- **CAP-5**
  - **intent:** HotSync is configured in `fujinet.yaml` and observable from the diagnostics console.
  - **success:**
    - A `hotsync:` block round-trips through the YAML store.
    - The service starts or stays off according to it.
    - A diagnostics command shows: running, last sync result and time, cradle state, and calendar state once CAP-6 exists.

- **CAP-6**
  - **intent:** A Palm's Date Book receives a one-way copy of a configured calendar on each sync, never altering appointments created on the Palm.
  - **success:** host tests cover the cases in `failure-modes.md`, and a sync against an ICS URL creates, updates and removes the matching Palm appointments.

## Constraints

- **No direct port access.** HotSync code never reads, writes or reconfigures the bus UART. The adapter that owns the channel lends it (see `cradle-sharing.md`). This is the upstream rule that rejected classic PR #1824.
- **NIO architecture rules.** No `#ifdef` in core, device, transport or config code; platform glue lives in `src/platform/<plat>/`. Constructor injection only, no globals. Shared code builds as gnu++17 (ESP32 GCC 8.4).
- **The core loop must not block.** HotSync sessions block on Palm replies for seconds and run for minutes, so the session runs outside `core.tick()`.
- **FujiBus as NIO defines it.** Palm apps use NIO wire semantics: status in `param[0]`, echoed command, NetworkDevice `0xFD`. No classic-command compatibility layer on FujiBus.
- **Memory.** A database is held whole during install or backup. Buffers are size-capped and go to PSRAM on ESP32.
- **Licence.** Code derived from palm-sync (Apache-2.0) carries its notice. No pilot-link (GPL) code.
- **Process.**
  - A new FujiBus command also ships its protocol doc, Python client support, a diagnostics provider and a `fujinet-nio-lib` call (`repos/fujinet-nio/AGENTS.md`).
  - `.gitmodules` URLs are unchanged, and workspace PRs carry no submodule pins.

## Non-goals

- Two-way record sync (Memo, Address, To Do) or Palm-to-calendar write-back.
- USB cradles, IrDA, Bluetooth, or Palm OS 5 network specifics beyond NetSync.
- A web UI. NIO has none; configuration is YAML plus the diagnostics console and CLI.
- Running unmodified classic Palm apps (classic `0x70`/`0x71` command set) against NIO.
- Google OAuth inside NIO for this spec; CAP-6 starts with ICS over HTTP(S).
- POSE/CloudpilotEmu serial-over-TCP on port 6416 as a separate listener. Emulators reach the normal serial path through a pty.

## Success signal

A Palm in a serial cradle on an FN-RS232 board running NIO does two things without reconfiguring anything in between:

- presses HotSync, receives a queued app, and is backed up;
- launches that app, which fetches data over FujiNet.

The same flows pass on POSIX NIO with CloudpilotEmu and `fake_palm.py`.

## Assumptions

- The FN-RS232 ESP32-S3 board (`rs232-esp32-s3-wroom-1-n16r8`) with a null-modem cradle is the reference hardware. RTS/CTS stay disabled for the cradle.
- CloudpilotEmu through a socat pty does not model baud mismatch, so baud-switch behaviour is proven only on the real cradle.
- A HotSync session and FujiBus app traffic never overlap. A Palm cannot run an app and HotSync at the same time.

## Decisions (formerly open questions)

Mark delegated these to dillera, who accepted the proposals on 2026-10-18.

- **Session model.** A long-lived platform task API, `platform::start_service_task()` (POSIX: detached pthread; ESP32: FreeRTOS task with an internal-RAM stack). The session stays blocking request/reply code; no poll-driven state machine.
- **"Sync now" command.** Not in v1. The cradle uses listening windows; revisit once CAP-4 runs on hardware.
- **Ownership of new commands.** No new FujiBus commands in v1. The install queue is filled through existing FileDevice writes to the persistent filesystem; status is diagnostics-only (`hotsync.status`).
- **Calendar sources.** ICS over HTTP(S) only for CAP-6. Google OAuth stays a non-goal.
- **Repository home.** Palm apps stay in `dillera/fujinet-palm` and consume `fujinet-nio-lib`.
