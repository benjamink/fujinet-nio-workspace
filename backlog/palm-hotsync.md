# Palm OS support (HotSync and Palm apps)

Status: `TODO`

## Goal

A Palm in a serial cradle on an FN-RS232 board running NIO can HotSync (install apps, back up, receive a calendar) and run Palm apps that use FujiNet over the same cradle. NetSync over Wi-Fi works too.

This is a clean re-implementation to NIO standards of dillera's classic fujinet-firmware work (branch `palm-demo-fozz`, FujiNetWIFI PR #1826).

Spec: [`_bmad-output/specs/spec-palm-hotsync/SPEC.md`](../_bmad-output/specs/spec-palm-hotsync/SPEC.md)

## Phase 0: design agreement

- [ ] Maintainer review of the spec. Settle its open questions: session task model, "sync now" command, owner of new commands, calendar sources, Palm app repo home.
- [ ] Break the agreed spec into stories (`stories.yaml`).

## Phase 1: protocol core (`fujinet-nio`), CAP-1

- [ ] Port the capture-based tests first, then implement SLP, PADP/CMP, NetSync, DLP, PDB/PRC and the session behind injected link, storage and clock interfaces.
- [ ] palm-sync Apache-2.0 notice in place.

## Phase 2: NetSync service, CAP-2 and CAP-5

- [ ] HotSync platform service on POSIX and ESP32, a `hotsync:` YAML block, and a diagnostics provider.
- [ ] Prove on POSIX with `fake_palm.py`, then on an FN-RS232 board with a real Palm's Network HotSync.

## Phase 3: Palm client (`fujinet-nio-lib`, Palm apps), CAP-3

Can run in parallel with phases 1 and 2.

- [ ] Palm stream target (prc-tools m68k, New Serial Manager byte channel, retry policy).
- [ ] FN Test on NIO over `fujibus-rs232` (no line sharing yet), then port the remaining apps.

## Phase 4: shared cradle, CAP-4

- [ ] Cradle channel adapter with a unit-tested hand-off state machine; injected baud control.
- [ ] FN-RS232 S3 env with the cradle enabled and no hardware flow control.
- [ ] Real cradle: button-press sync, then an app session, with no reconfiguration in between.

## Phase 5: Date Book conduit, CAP-6

- [ ] One-way ICS calendar to Date Book with every case in `failure-modes.md` covered by host tests.

## Dependencies

- RS-232 pacing defaults from `amiga-rs232-38400-reliability.md` apply to any RS-232 host. Confirm they suit 115200 to a Palm.
- Multi-link operation is future work in `repos/fujinet-nio/docs/architecture.md`. This goal uses one channel, shared by an adapter.
