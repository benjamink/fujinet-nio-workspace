# Workbench 1.3 integration coverage

Workbench 1.3 is a primary target.  A test which has a shared behavioural
contract with newer Workbench releases should have one pytest module and a
`wb13` environment variant in `integration-tests/amiberry/tests.toml`.
The variant supplies a 1.3 Shell-safe startup sequence, static MountList setup,
and `amiga_artifact_profile = "wb13"`.  It is only enabled after the guest
case passes; an omitted `wb13` environment is an explicit coverage gap, not a
pass or skip.

## Established coverage

* `test_amiga_fin_slot_catalog.py` runs on WB1.3 and WB3.2.
* `test_wifi_config.py` runs on WB1.3 and WB3.2.
* `test_diskdevice_loader.py` runs on WB1.3 and WB3.2.
* `test_diskdevice_wb13.py` exercises static-unit lifecycle, multi-drive
  reads/writes/copy, readonly media and all eight `DN` units.
* `test_nio_wb13.py` proves the cold serial-worker load path.

## Current porting findings

### Stateful CLI (`test_cli_stateful.py`)

This is not enabled for WB1.3 yet.  The WB1.3-profiled `FHOST host:/` and
subsequent `FHOST` complete successfully.  The following profiled `FLS host:/`
never submits a FileDevice request: the NIO log contains the three Host-device
exchanges and no FileDevice exchange.  Increasing the Shell stack from 4096
to 8192 bytes does not change that outcome.  This is an application/runtime
fault to diagnose, not a Workbench 1.3 redirection issue; WB1.3 redirection
was already written in the required form, `FLS >DH0:result host:/`.

### FFS and high-density media

The WB1.3 static MountList currently declares DD/OFS geometry.  The WB3.2 FFS
and HD cases depend on dynamic DosNodes or geometry-specific MountList entries.
An experimental DN0: entry with `DosType = 0x444F5301` and
`FileSystem = L:FastFileSystem` allowed `FMOUNT` to report success but the
first `Dir DN0:` raised WB1.3's **“Not a DOS disk in unit 0”** requester.  It
was deliberately not retained.  Port these cases only alongside a deliberate
static FFS/HD MountList design and a guest fixture that proves the filesystem
handler is registered.  Do not claim the current DD static entry can validate
either media type.

### Dynamic-DOS-node and removal tests

WB1.3 has no public DOS-list locking/dynamic DosNode API.  Cases whose
assertion is creation/removal of a dynamic node (including unload/reload and
handler-removal tests) cannot be direct WB1.3 ports.  Their WB1.3 equivalent
is static DN0:--DN7: medium replacement/eject coverage, which belongs in
`test_diskdevice_wb13.py`.

## Remaining pytest modules: porting disposition

| Module(s) | Disposition |
| --- | --- |
| `test_amiga_fin_slot_catalog.py`, `test_wifi_config.py`, `test_diskdevice_loader.py` | Shared WB3.2/WB1.3 case variants are enabled and pass. |
| `test_diskdevice_wb13.py`, `test_nio_wb13.py` | WB1.3-native acceptance modules already pass. |
| `test_cli_stateful.py` | Blocked by the profiled `FLS` runtime fault described above. `FHOST` is proven; do not enable a partial stateful contract. |
| `test_amiga_fin_ffs_adf.py` | Blocked pending a proven WB1.3 FFS handler-registration/static MountList design. |
| `test_checksumbench.py` | Blocked: the WB1.3-profiled application reaches the OS **task held** requester. This needs an application/runtime fix, not a test-script variant. |
| `test_diskdevice_adf.py`, `test_diskdevice_fmount.py`, `test_diskdevice_fmount_restore.py`, `test_diskdevice_fumount_handler.py`, `test_diskdevice_inhibit.py`, `test_diskdevice_inhibit_experiments.py`, `test_diskdevice_unload_reload.py` | Their exact contracts assert dynamic node creation/removal, handler lifecycle, or `FMOUNTRESTORE`; WB1.3 uses static MountList handlers. Extend `test_diskdevice_wb13.py` for equivalent user-visible static-media contracts rather than duplicate invalid assertions. |
| HD-specific nodes in `test_diskdevice_adf.py` and `test_diskdevice_fmount.py` | Blocked on a static HD MountList profile; the DD configuration must not pretend to cover HD. |
| `test_diskdevice_mapping_failure.py`, `test_diskdevice_silent_timeout.py`, `test_inspect_causal*.py` | These inspect dynamic DOS/handler state or targeted failure recovery. First specify the observable WB1.3 static-handler equivalent; they are not mechanical Shell ports. |
| `test_nio_broker.py`, `test_nio_paula_serial.py`, `test_nio_native_test.py` | Need a profile-aware broker/native-tool build path. The present `nio_broker` fixture invokes the unprofiled native build, so claiming WB1.3 coverage would test the wrong artifact. |
| `test_harness_completion.py` | Host harness coverage, not a guest Workbench capability. |
