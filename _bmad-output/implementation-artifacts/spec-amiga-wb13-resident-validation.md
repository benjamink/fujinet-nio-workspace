---
title: 'Repeatable Workbench 1.3 resident validation'
type: 'feature'
created: '2026-09-27'
status: 'in-progress'
baseline_commit: 'e1b3c427580a8bdf0cbe129a0873f636734f3044'
review_loop_iteration: 0
context:
  - 'docs/agent-test-policy.md'
  - 'docs/amiga/amiberry-testing.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Jeff's Kickstart 1.3 resident-tag and device-node fixes were demonstrated manually, but no repeatable artifact check protects the emitted tags in all three real device binaries. The existing interactive `wb1.3` profile also lacks the licensed-media setup and development-share contents needed to repeat the cold broker experiment conveniently.

**Approach:** Add an artifact-level native-build gate for the three resident device binaries, make the existing `wb1.3` interactive profile usable with Amiga Forever 1.3 media and current diagnostics, and document a controlled cold-start procedure that proves the worker—not a prior serial open—loads stock `serial.device`.

## Boundaries & Constraints

**Always:** Keep licensed Amiga Forever paths solely in ignored `local/amiga.env`; retain the A500/68000-compatible WB1.3 profile; ensure the cold proof never preloads or opens `serial.device`; test real cross-built artifacts rather than native-test compilation variants; use the smallest relevant driver build/test and one manual Amiberry launch.

**Ask First:** Change the selected 512 KiB A500 memory profile or create a disposable automated WB1.3/HDF environment.

**Never:** Commit licensed ROM/ADF/key material; add the cold validation to `Startup-Sequence`; treat a reset inside an already-running emulator as a cold boot; run the full Amiberry suite by default.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|---------------------------|----------------|
| Resident artifact | Each production `.device` binary | ROMTag is in `.text`; self-match and `rt_EndSkip` relocation/offset are valid | Gate fails naming the device and invalid field |
| Device-node runtime | Fresh KS1.3 Workbench | Loader can register and subsequent `OpenDevice` resolves name | Guest procedure records failure and stops |
| Cold serial load | New Amiberry process; `serial.device` unopened | First broker exchange succeeds and returns a clock response | Preserve logs/screenshot; do not warm up and retry in same process |
| Missing licensed media | WB13 variables absent | Launcher explains missing media/key path | No fallback or committed local path |

</frozen-after-approval>

## Code Map

- `repos/fujinet-nio-driver/amiga/Makefile` -- production device targets; add a cross-artifact resident gate after all three real binaries build.
- `repos/fujinet-nio-driver/amiga/tools/fujinet-load-resident.c` -- defines the runtime ROMTag acceptance contract; its first-hunk scanner informs artifact assertions but cannot be reused directly on unrelocated HUNK files.
- `repos/fujinet-nio-driver/amiga/{disk.device,nio.device,serial.device}/*device*.c` -- owns the three emitted `device_resident` tags and KS1.3 node initialization.
- `configs/amiga/workbenches.yaml` -- existing direct-floppy `wb1.3` profile; opt it into the read-only NIO development share and consume the optional ROM-key variable.
- `tools/build/nio_build/amiga_config.py` -- refreshes `build/amiga-share`; add `fujinet-nio-exchange` so the cold diagnostic is reachable as `NIO:`.
- `local/amiga.env.example` and `docs/amiga/{environment-setup,amiberry-testing}.md` -- document variables and exact interactive verification without storing local licensed paths.

## Tasks & Acceptance

**Execution:**

- [x] `repos/fujinet-nio-driver/amiga/Makefile` and a focused host artifact-test helper -- inspect real cross-linked device ROMTags with the installed m68k toolchain; verify every changed `rt_EndSkip` contract.
- [x] `configs/amiga/workbenches.yaml` and `tools/build/nio_build/amiga_config.py` -- make `wb1.3` mount current NIO artifacts, including the exchange diagnostic, and pass a configured Amiga Forever ROM key.
- [x] `local/amiga.env.example`, `docs/amiga/environment-setup.md`, and `docs/amiga/amiberry-testing.md` -- document WB1.3 media variables and an isolated cold-process procedure.
- [x] ignored `local/amiga.env` -- configure the user-supplied AF11 ROM, matching key, and Workbench 1.3 ADF after verifying they are readable.

**Acceptance Criteria:**

- Given the three production devices were cross-built, when the resident-artifact gate runs, then it fails if any `rt_EndSkip` is not the relocated address immediately past that device's ROMTag.
- Given the `wb1.3` profile and configured local media, when interactive Workbench launches, then `NIO:` contains the loader, broker device, and exchange tool.
- Given a newly launched WB1.3 Amiberry process with no previous serial open, when the loader registers only `fujinet-nio.device` and the exchange diagnostic sends its first request, then the exchange succeeds through stock disk-based `serial.device`.

## Spec Change Log

## Design Notes

The artifact gate deliberately complements, rather than replaces, guest behavior: linked HUNK layout is the failure Jeff fixed, while KS1.3 `InitResident` and ramlib behavior require the guest procedure. The profile remains an interactive floppy session because `wb13` environment assembly is explicitly TBD.

## Verification

**Commands:**

- `source scripts/env.sh && make -C repos/fujinet-nio-driver/amiga native` -- all production Amiga devices and diagnostic tools build.
- `source scripts/env.sh && make -C repos/fujinet-nio-driver/amiga resident-artifacts` -- all three emitted ROMTags satisfy the gate.
- `source scripts/env.sh && make -C repos/fujinet-nio-driver/amiga tests` -- existing fast Amiga driver contract suite passes.
- `source scripts/env.sh && uv run --project tools/build pytest tools/build/tests/test_amiga_shares.py` -- development-share behavior passes its focused host tests.

**Manual checks:**

- Start a new `wb1.3` Amiberry process using the documented command; do not preload stock `serial.device`. Load only the broker and run one cold exchange; record successful output and confirm a second, separately launched process behaves identically.
