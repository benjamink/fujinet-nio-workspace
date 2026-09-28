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
* `test_cli_stateful.py` runs on WB1.3 and WB3.2.
* `test_diskdevice_wb13.py` exercises static-unit lifecycle, multi-drive
  reads/writes/copy, readonly media and all eight `DN` units.
* `test_nio_wb13.py` proves the cold serial-worker load path.

## Current porting findings

### Stateful CLI (`test_cli_stateful.py`)

The shared case is enabled and captures the native output of `FHOST`, `FLS`,
and `FAPP` through WB1.3 command-output redirection.  The required `Wait 3`
is immediately after `fujinet-load-resident`: without it, the first new client
can finish its NIO request but the StartupII command chain does not reliably
advance.  An interactive `Execute` script and a focused StartupII probe both
prove `FLS >DH0:file` and `FHOST >DH0:file` are valid.  Therefore this is a
cold resident-worker readiness/lifecycle issue, not a WB1.3 Shell-redirection
limitation.  The test proves Host, FileDevice, and AppStore exchanges in order.

### FFS and high-density media

The default WB1.3 static MountList declares DD/OFS geometry. The mixed profile
now supplies static `HD0:`--`HD3:` handlers (units 4--7, 22 blocks/track),
with `DN0:`--`DN3:` retaining DD geometry. The mixed-profile acceptance case
proves concurrent DD/HD read/write copy, HD eject, remount, and persistence.
The WB3.2 FFS cases still depend on a registered FFS handler.
An experimental DN0: entry with `DosType = 0x444F5301` and
`FileSystem = L:FastFileSystem` allowed `FMOUNT` to report success but the
first `Dir DN0:` raised WB1.3's **“Not a DOS disk in unit 0”** requester.  It
was deliberately not retained. Port the FFS case only alongside a deliberate
static FFS MountList design and a guest fixture that proves the filesystem
handler is registered.

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
| `test_cli_stateful.py` | Shared WB3.2/WB1.3 case variant is enabled; it waits for cold resident-worker readiness before the first client. |
| `test_amiga_fin_ffs_adf.py` | Blocked pending a proven WB1.3 FFS handler-registration/static MountList design. |
| `test_checksumbench.py` | Blocked: the WB1.3-profiled application reaches the OS **task held** requester. This needs an application/runtime fix, not a test-script variant. |
| `test_diskdevice_adf.py`, `test_diskdevice_fmount.py`, `test_diskdevice_fmount_restore.py`, `test_diskdevice_fumount_handler.py`, `test_diskdevice_inhibit.py`, `test_diskdevice_inhibit_experiments.py`, `test_diskdevice_unload_reload.py` | Their exact contracts assert dynamic node creation/removal, handler lifecycle, or `FMOUNTRESTORE`; WB1.3 uses static MountList handlers. Extend `test_diskdevice_wb13.py` for equivalent user-visible static-media contracts rather than duplicate invalid assertions. |
| HD-specific nodes in `test_diskdevice_adf.py` and `test_diskdevice_fmount.py` | User-visible concurrent DD/HD static media is covered by `test_diskdevice_wb13.py`; dynamic-node assertions remain WB2+ only. |
| `test_diskdevice_mapping_failure.py`, `test_diskdevice_silent_timeout.py`, `test_inspect_causal*.py` | These inspect dynamic DOS/handler state or targeted failure recovery. First specify the observable WB1.3 static-handler equivalent; they are not mechanical Shell ports. |
| `test_nio_broker.py`, `test_nio_paula_serial.py`, `test_nio_native_test.py` | Need a profile-aware broker/native-tool build path. The present `nio_broker` fixture invokes the unprofiled native build, so claiming WB1.3 coverage would test the wrong artifact. |
| `test_harness_completion.py` | Host harness coverage, not a guest Workbench capability. |
