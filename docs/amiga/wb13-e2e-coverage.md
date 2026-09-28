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
