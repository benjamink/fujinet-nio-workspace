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
* `test_checksumbench.py` runs on WB1.3 and WB3.2.
* `test_diskdevice_wb13.py` exercises static-unit lifecycle, multi-drive
  reads/writes/copy, readonly media and all eight `DN` units.
* `test_nio_wb13.py` proves the cold serial-worker load path.
* `test_nio_broker.py`, `test_nio_native_test.py::test_native_test_clock_exchange`,
  and `test_nio_paula_serial.py` run against the WB1.3 artifact profile.
* `test_diskdevice_wb13.py::test_wb13_mount_times_out_against_stalled_external_peer`
  proves that a serial peer which accepts a connection but does not complete a
  FujiBus reply produces the normal bounded `FMOUNT` failure (`RC=20`), not a
  Guru requester.

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

### Checksum benchmark (`test_checksumbench.py`)

`timer.device` can be opened on WB1.3, but `ReadEClock()` is a V36
(Workbench 2.0) interface, not a V34 one. Calling it through WB1.3's timer
library vector produced the **“Software error -- task held”** requester before
the benchmark emitted a row. The newer-artifact path now calls it only when
`TimerBase->dd_Library.lib_Version >= 36`; otherwise it uses
`TR_GETSYSTIME` through the opened `timerequest` with `DoIO()`, yielding a
1 MHz microsecond clock. The WB1.3 artifact always uses that compatible
command-clock path and 32-bit modular tick differences, which are sufficient
for each short timing interval and avoid unnecessary 64-bit arithmetic on the
68000 path.

The WB1.3 artifact retains all six buffer sizes and C/ADDX/branch checksum
implementations, with one tenth of the existing iteration counts so the
acceptance run is practical at real A500 speed. Its StartupII sequence also
places output redirection before the `FLS` path, as required by Shell 1.3.
The shared assertion verifies all 18 rows. Verified 2026-09-28 with
`scripts/amiga-tests --amiga-env wb13 --amiga-machine a500-000
test_checksumbench.py -q` (pass, 36.21 s) and the unchanged WB3.2 case
(`--amiga-env wb32 --amiga-machine a1200-030`, pass, 11.45 s).

### Stalled external serial peer (`test_diskdevice_wb13.py`)

The static-handler mount timeout case originally raised WB1.3's **“Software
error -- task held”** requester.  This was not a DiskDevice worker stack
shortage: retaining the original 16 KiB worker stacks and mapping the fault
placed it at entry to the NIO serial backend.  The 68000 call had received an
invalid trailing diagnostic-output pointer (`0xfc081a`) while the response
length pointer and the request itself were valid.  The backend was therefore
faulting before it could return the expected timeout.

The production device now calls the serial backend with only the response
length as a caller-owned output and obtains detail/native-I/O diagnostics from
backend-owned state immediately after the exchange.  This retains the
diagnostic contract without passing the three unsafe trailing pointers through
the KS1.3 serial-worker call.  The host native-device tests cover the original
callback diagnostic contract; the guest case is the regression proof for the
real serial ABI.

Verified 2026-09-28 with the original stack sizes:

`scripts/amiga-tests --amiga-env wb13 --amiga-machine a500-000
test_diskdevice_wb13.py::test_wb13_mount_times_out_against_stalled_external_peer -q`

and the unchanged WB3.2 control:

`scripts/amiga-tests --amiga-env wb32 --amiga-machine a1200-030
test_diskdevice_silent_timeout.py -q`.

### Native exchange matrix (WIP)

The larger `nio-native-exchange` matrix now has a WB1.3 startup sequence with
redirection before arguments and an explicit post-load readiness delay. Its
first run still times out before the native endpoint records a valid FujiBus
request; the console reaches the deliberately-invalid command usage probes,
but no Guru is raised. Do not enable it as accepted WB1.3 coverage yet. The
next investigation should inspect the first valid `fujinet-nio-exchange`
invocation and its command-line/worker boundary rather than reworking output
redirection. Rejected experiments: disabling optional elapsed-time setup and
forming the `OpenDevice` IORequest like the small native probe did not alter
the timeout; reducing the tool's 16 KiB stack to 4 KiB made it exit before its
first result checkpoint. The 16 KiB stack is therefore required for this tool
and remains unchanged.

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
| `test_checksumbench.py` | Shared WB3.2/WB1.3 case variant is enabled; WB1.3 uses the timer-device command clock rather than the unavailable `ReadEClock()` vector. |
| `test_diskdevice_adf.py`, `test_diskdevice_fmount.py`, `test_diskdevice_fmount_restore.py`, `test_diskdevice_fumount_handler.py`, `test_diskdevice_inhibit.py`, `test_diskdevice_inhibit_experiments.py`, `test_diskdevice_unload_reload.py` | Their exact contracts assert dynamic node creation/removal, handler lifecycle, or `FMOUNTRESTORE`; WB1.3 uses static MountList handlers. Extend `test_diskdevice_wb13.py` for equivalent user-visible static-media contracts rather than duplicate invalid assertions. |
| HD-specific nodes in `test_diskdevice_adf.py` and `test_diskdevice_fmount.py` | User-visible concurrent DD/HD static media is covered by `test_diskdevice_wb13.py`; dynamic-node assertions remain WB2+ only. |
| `test_diskdevice_silent_timeout.py` | Its static-handler equivalent is enabled as `test_wb13_mount_times_out_against_stalled_external_peer` in `test_diskdevice_wb13.py`; it proves the same bounded `FMOUNT` timeout against an external stalled peer. |
| `test_diskdevice_mapping_failure.py`, `test_inspect_causal*.py` | These inspect dynamic DOS/handler state or targeted failure recovery. First specify the observable WB1.3 static-handler equivalent; they are not mechanical Shell ports. |
| `test_nio_broker.py`, `test_nio_paula_serial.py`, `test_nio_native_test.py::test_native_test_clock_exchange` | Profile-aware WB1.3 variants are enabled and verified on the A500/KS1.3 environment. The native-test clock case checks the profile-specific native device map as well as its exchange. The larger native disk/fault matrix is the next porting candidate. |
| `test_harness_completion.py` | Host harness coverage, not a guest Workbench capability. |
