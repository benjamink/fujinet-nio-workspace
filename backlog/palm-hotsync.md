# Palm OS support (HotSync and Palm apps)

Status: `IN PROGRESS` (phases 1, 2 and 4 done; cradle HotSync proven on an FN-RS232 with a real Palm; phases 3 and 5 open)

## Goal

A Palm in a serial cradle on an FN-RS232 board running NIO can HotSync (install apps, back up, receive a calendar) and run Palm apps that use FujiNet over the same cradle. NetSync over Wi-Fi works too.

This is a clean re-implementation to NIO standards of dillera's classic fujinet-firmware work (branch `palm-demo-fozz`, FujiNetWIFI PR #1826).

Spec: [`_bmad-output/specs/spec-palm-hotsync/SPEC.md`](../_bmad-output/specs/spec-palm-hotsync/SPEC.md)

## Phase 0: design agreement

- [x] Maintainer review of the spec. Mark delegated the open questions to dillera; decisions recorded in the spec.
- [ ] Break the agreed spec into stories (`stories.yaml`).

## Phase 1: protocol core (`fujinet-nio`), CAP-1

- [x] Port the capture-based tests first, then implement SLP, PADP/CMP, NetSync, DLP, PDB/PRC and the session behind injected link, storage and clock interfaces. (`fujinet-nio` `feat/palm-hotsync`, `tests/test_hotsync.cpp`)
- [x] palm-sync Apache-2.0 notice in place (`docs/hotsync.md`).

## Phase 2: NetSync service, CAP-2 and CAP-5

- [x] HotSync platform service on POSIX and ESP32, a `hotsync:` YAML block, and a diagnostics provider.
- [x] Prove on POSIX with `fake_palm.py` (install and backup).
- [ ] Prove on an FN-RS232 board with a real Palm's Network HotSync. On 2026-10-18 `fake_palm.py` synced over Wi-Fi with an FN-RS232 S3 (install and backup to `sd0:/hotsync`); the Palm at hand has no network, so a real NetSync is still unproven.
- [x] Console settings: `hotsync.get`, `hotsync.set`, `hotsync.save`.

## Phase 3: Palm client (`fujinet-nio-lib`, Palm apps), CAP-3

Can run in parallel with phases 1 and 2.

- [ ] Palm stream target (prc-tools m68k, New Serial Manager byte channel, retry policy).
- [ ] FN Test on NIO over `fujibus-rs232` (no line sharing yet), then port the remaining apps.

## Phase 4: shared cradle, CAP-4

- [x] Cradle channel adapter with a unit-tested hand-off state machine; injected baud control. (`hotsync::CradleChannel`, `io::BaudControl`; `fujinet-nio` 9e414b3)
- [x] FN-RS232 S3 with the cradle enabled and no hardware flow control. Enabled by config (`hotsync.cradle`, console `hotsync.set cradle 1`) rather than a separate env; the board's `channel.uart.flow_control` was already `none`.
- [x] Real cradle: button-press sync, then an app session, with no reconfiguration in between. 2026-10-18, FN-RS232 S3 (`fujibus-gpio-rs232-cdc-log-s3-wroom-1-n16r8`): two button-press syncs (10 databases backed up; FN Test and FujiNet Config installed), then FN Test's FujiBus ping reached NIO through the cradle (`cradle_fujibus_packets: 1`, cradle held for the app). The ping showed "Error 8002" because that FN Test is the classic build; NIO's reply is phase 3's to handle.
- Emulator rig for repeat runs: CloudpilotEmu `--serial` <-> socat pty pair <-> POSIX `fujibus-rs232-debug` (see `repos/fujinet-nio/docs/hotsync.md`, "Testing with an emulator").

## Phase 5: Date Book conduit, CAP-6

- [ ] One-way ICS calendar to Date Book with every case in `failure-modes.md` covered by host tests.

## Dependencies

- RS-232 pacing defaults from `amiga-rs232-38400-reliability.md` apply to any RS-232 host. Confirm they suit 115200 to a Palm.
- Multi-link operation is future work in `repos/fujinet-nio/docs/architecture.md`. This goal uses one channel, shared by an adapter.
