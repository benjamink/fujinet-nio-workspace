# FUMOUNT multi-node investigation

Status: open, observed 2026-09-27.

This log preserves the investigation into the failure to unmount `DN0:` after
the normal writable `DN2:` mount, unmount and remount path. It is deliberately
separate from the disk-media architecture: it records evidence and rejected
experiments, not a change to the supported-media contract.

## Reproducer

The existing `diskdevice-fmount` Amiberry scenario executes this order:

1. Mount and use catalogue media on `DN0:`; including DD/HD replacement.
2. Mount writable catalogue slot 13 on `DN2:`, write `PERSIST.TXT`, then
   `FUMOUNT DN2:` successfully.
3. Remount slot 13 on `DN2:` and verify the persisted file.
4. Run `FUMOUNT DN0:`.

The final command fails in a fresh WB3.2/A1200 serial run:

```text
Cannot retire DN0: handler (busy)
FUMOUNT RC=10
```

Exact command:

```sh
source scripts/env.sh
scripts/amiga-tests --amiga-env wb32 --amiga-machine a1200-030 \
  test_diskdevice_fmount.py -k 'fmount_fumount_standard_adf and serial' -vv
```

The dedicated `test_diskdevice_fumount_handler.py` still passes. It proves
ordinary idle unmount, live-handler unmount, and the intentional refusal while
`CD DN0:` holds a real resource, but it does not create then remount a second
dynamic DosNode before retiring `DN0:`.

## Current diagnosis

`FUMOUNT` flushes the handler, submits `ACTION_DIE`, and only ejects after
the handler has set the device node's `dol_Task` to null. In this case FFS
rejects `ACTION_DIE` with `ERROR_OBJECT_IN_USE` (202), so the fail-closed
command correctly does not eject media or remove the `DN0:` DosList entry.

The AmigaDOS Kernel Reference Manual says that `ACTION_DIE` must fail when a
handler cannot safely release resources that can retain its message port
(including locks, file handles and notification requests). It also cautions
that cached handler ports make termination inherently unsuitable as a general
forced-unmount primitive. Do not turn this failure into a forced `TD_EJECT`:
that can leave a live FFS handler attached to removed media.

At the point immediately after the second `FMOUNT 13 DN2: RW`, DOS-list
diagnostics showed the new `DN2:` node with `dol_Task == 0`; it had not yet
started an FFS handler. Thus the trigger is not a normal open file, directory
lock or live `DN2:` handler. The condition is produced by the presence of the
second dynamic FFS node itself (or state FFS associates with it).

The guest-side `lockdiag` run after the final failed `FUMOUNT DN0:` found both
`DN0` and `DN2` as waiting filesystem processes, but found no process whose
`pr_CurrentDir`, `pr_HomeDir`, `pr_CIS`, `pr_COS`, or `pr_CES` handler pointed
at `DN0`'s port. This rules out the usual shell current-directory lock and the
standard input/output/error streams. The next run also dumps every public
volume entry and its `dol_LockList`, rather than only entries whose task port
still matches the live handler: a stale or detached volume entry is itself
relevant to an `ACTION_DIE` refusal.

The temporary failure-only `FUMOUNT` diagnostic captured the handler reply in
the normal serial reproducer: `ACTION_DIE` returned false with `IoErr=202`
(`ERROR_OBJECT_IN_USE`). This is direct evidence that FFS refuses the request;
the later unchanged `dol_Task` is a consequence, not the original failure.

The expanded volume diagnostic then captured a failed run in
`amiberry-20260927-192357`. It found only `NIOADF` for the live `DN2:` handler
and its `dol_LockList` was empty; no volume entry pointed at the still-live
`DN0:` handler. Thus neither a public volume lock nor a stale public DN0
volume entry accounts for the refusal. The remaining candidates are an
otherwise-unreachable file handle/lock or FFS-private handler state.

The WIP reduced scenario `diskdevice-fumount-multinode-minimal` failed in
`amiberry-20260927-192759` with the same `ACTION_DIE` / `IoErr=202` result.
It contains one DN0 mount/use only—no DD/HD replacements—followed by the DN2
writable mount, FUMOUNT, remount and persistence read. Therefore DN0 media
replacement history is not a prerequisite; the DN2 lifecycle alone triggers
the condition.

## Timeline and historical coverage

| Date | Commit | Change | Relevance |
| --- | --- | --- | --- |
| 2026-08-13 | `2adeaf711` | Added the initial `diskdevice-fmount` test with a final `FUMOUNT DN0:` assertion. | Only single-node coverage at introduction. |
| 2026-08-14 | `9a312ba6` | Added writable `DN2:` mount → `FUMOUNT DN2:` → remount → persistence, ahead of the existing final `FUMOUNT DN0:`. | This is the essential multi-node path, and it asserted both unmounts. |
| 2026-08-16 | `563a70cb` | Switched the sequence from explicit DOS `Mount` calls to direct `FMOUNT` starts. | Established the current command shape. |
| 2026-08-19 | `e105c49d` | Removed `Assign DN2: DISMOUNT` and its interactive diagnostic gate. | Established the current user-journey path. |
| 2026-09-03 | `a03090ac` in `nio-core-apps` | Replaced inhibit/keep-handler eject with `ACTION_DIE`, wait for `dol_Task == 0`, then eject. | Introduced the current teardown model. |
| 2026-09-03 | `158e48ff`, `542af6cc` in `nio-core-apps` | Removed successful nodes from the DosList and tightened error handling. | Established the current node-removal contract. |
| 2026-09-16 | `0a77bd26` | Recorded **65 passed, no skips** on WB3.2/A1200; the suite included `test_fmount_fumount_standard_adf`. | Strong evidence that this exact scenario passed after the September teardown changes. |
| 2026-09-17 | `04c162085` | Ran the scenario for serial and native installations. | The test sequence and assertions were unchanged. |
| 2026-09-27 | `6bc98080` in `nio-core-apps` | Added a `__KICK13__` static-MountList branch to `fmount.c`. | The existing WB3.2 branch is unchanged. |

The September 16 acceptance record points to
`test-evidence/amiberry-20260916-233252/`, but that evidence directory is not
present in this checkout. The historical pass is therefore a recorded result,
not independently re-read artifact evidence in this session.

## 2026-09-27 historical-workspace reconstruction

An independent detached clone was created at workspace commit `0a77bd26` and
all submodules were initialised at that commit's recorded gitlinks:

- `fujinet-nio-driver`: `d7d65934cf0dec1f1610f9b37c245ea0df3f4abb`
- `nio-core-apps`: `cdb026d28f53254459824591ec6439db108804e6`

It built a fresh `wb32/a1200-030` base HDF from the locally configured,
licensed Workbench 3.2 media and ran the exact historical test node:

```sh
scripts/amiga-tests --amiga-env wb32 --amiga-machine a1200-030 \
  test_diskdevice_fmount.py::test_fmount_fumount_standard_adf -vv
```

The old source requires three **disposable reconstruction-only** includes of
`<dos/dos.h>` (in `fujinet_serial_device.c`, `fujinet-nio-baud.c`, and
`fujinet-nio-serial.c`) to compile with the current NDK headers. They provide
the missing `BPTR` and `RETURN_*` declarations only; no disk-device,
`FMOUNT`, or `FUMOUNT` source was changed.

The guest booted and loaded both resident devices, but stopped before the
mount/unmount sequence with `Unsupported candidate media`. Its completion
monitor found no test completion marker. Therefore this run is neither a
historical passing proof nor a reproduction of the current final-`DN0:`
failure: the regenerated present-day test-media/environment does not satisfy
the historical disk-media contract. Its artifacts are intentionally isolated
under `/tmp/nio-fumount-20260916-Bdmn72/`, not in the workspace evidence tree.

## What changed after the recorded pass?

No change found that should alter this WB3.2 path:

- The `diskdevice-fmount` startup sequence is unchanged since `e105c49d`.
- The test assertions are unchanged; `04c162085` only parameterised them for
  serial/native installation.
- `fumount.c` is unchanged since `542af6cc`.
- The only post-September-16 `fmount.c` change is inside `#ifdef __KICK13__`.
  The WB3.2 dynamic-DosNode code compiled by this reproducer is unchanged.
- The post-September-16 disk-device difference is likewise a Kickstart-1.3
  initialization/ROMTag correction, excluded from the normal WB3.2 path.

This means the present evidence does **not** identify a source regression.
Either the September 16 run depended on state not represented in the current
isolated reproducer, or its broad-suite result did not expose this exact
failure despite executing the named test. The next investigation should
compare a preserved September 16 HDF/result artifact, if recovered, against a
current generated HDF before changing production behaviour.

## Experiments rejected

| Experiment | Result | Reason not adopted |
| --- | --- | --- |
| Observe retirement for 100 ticks (about two seconds) after `ACTION_DIE` | Final `DN0:` still failed. | This is not merely a short `dol_Task` clearing delay. |
| Add temporary `DoPkt` result/`IoErr()` diagnostics | One run passed, but isolated reruns with only result capture or only `IoErr()` still failed. | The pass was nondeterministic; no diagnostic side effect is a fix. |
| Amiberry DOS-handler packet trace for `DN0` and `DN2` | Captured `DN0` as a real active FFS process/port (`0x258948` / `0x2589a4`) while DOS separately held a `DN2` task port (`0x260a8c`), then Amiberry reset its IPC socket during the full task-list walk. | Confirms the active handler is real, but the current controller is too chatty to identify the final packet reliably. |
| Bounded `PutMsg`/`ReplyMsg` controller | It resolved `DN0:` and `DN2:` ports but lost the debugger socket before a packet was captured. One instrumented run passed; the immediately following uninstrumented run failed with `IoErr=202`. | The debugger changes scheduling and the pass is not evidence of a fix. Retain the controller only as WIP diagnostic infrastructure; do not use it for acceptance. |
| Public volume-lock scan | In failed run `amiberry-20260927-192357`, DN2's `NIOADF` volume had `dol_LockList=0`; no volume entry referred to live DN0. | Eliminates the remaining public volume lock chain and stale-volume theory. |
| Resolve `dol_Task` directly instead of `DeviceProc("DN0:")` | The exact serial scenario still failed with `ACTION_DIE` / `IoErr=202` (`amiberry-20260927-192529`). | `DeviceProc` is not creating the retained resource; production code remains unchanged. |
| Minimal multi-node scenario | A single DN0 mount/use followed by DN2 writable mount → FUMOUNT → remount → persisted Type still refused DN0 `ACTION_DIE` (`amiberry-20260927-192759`). | DN0 replacement history is eliminated; split DN2 teardown from remount next. |
| Start `DN2:` eagerly with `ADNF_STARTPROC` | Final `DN0:` retirement still failed. | Changes the documented lazy-node model without fixing it. |
| Remove volume entries manually after handler retirement | No improvement. | FFS owns its volume entries; manual removal is unsafe. |
| Delay after `FUMOUNT DN2:` | A three-second delay did not change the failure. | Not a handler-exit timing race. |
| `Inhibit(TRUE)` before `ACTION_DIE` | Guest run hung. | Unsafe lifecycle ordering. |
| `Assign DN0: DISMOUNT` workaround | Removes the node before `FUMOUNT` can finish cleanup. | Reintroduces a non-standard, partial state. |
| Ignore `ACTION_DIE` and issue `TD_EJECT` | Not implemented. | Contradicts the fail-closed AmigaDOS resource contract. |

## Next evidence to obtain

1. Reduce the sequence with `diskdevice-fumount-multinode-minimal`: one
   DN0 mount/use, then DN2 writable mount/unmount/remount, then DN0 FUMOUNT.
   Its result separates DN0 replacement history from the second dynamic node.
2. Recover and inspect `amiberry-20260916-233252` if available outside this
   checkout. Confirm the actual `fumount-eject.result` and exact binaries in
   the HDF.
3. Recover the exact September media fixture/configuration too, then rerun the
   already reconstructed workspace rather than substituting regenerated media.
4. Capture the complete `ACTION_DIE` transaction without the former full
   task-list scan. `AMIGA_E2E_FUMOUNT_DIE_TRACE=1` enables the bounded host
   controller. It refreshes only the `DN0:`/`DN2:` DosList ports, waits for a
   selected port to exist, then records the matching `PutMsg` and `ReplyMsg`
   packet result. This avoids stopping all Workbench startup traffic and
   distinguishes an FFS refusal from a caller-side observation error without
   changing guest lifecycle behaviour.
5. If both old and current revisions reproduce the failure with equivalent
   media, treat it as a previously unobserved FFS multi-DosNode limitation.
   Choose a new explicit FUMOUNT contract before implementation; do not
   silently force eject.
