# Workbench 1.3 multi-drive investigation

Status: work in progress.

## Confirmed behaviour

The WB1.3 `DN0:` lifecycle passes when the static handler is started before
using `FMOUNT`: mount slot 11, read `KNOWN.TXT`, `FUMOUNT`, remount, and read
again.

For concurrent static handlers, the following is also confirmed on the
`wb13-a500` Amiberry environment:

1. start `DN0:` and `DN2:` with `Mount` after loading the resident disk
   device;
2. mount slot 11 on `DN0:` and read it;
3. mount writable slot 13 on `DN2:`;
4. copy a file from `DH0:` to `DN2:`; and
5. eject `DN2:` with `FUMOUNT`.

The driver reports `STATUS drive=2 change=1 absent=0 protected=0` after the
DN2 map, proving that the media is present and writable at the trackdisk
device layer.

## Outstanding failure

After `FUMOUNT DN2:`, `FMOUNT 13 DN2: RW` maps the same media successfully,
but `Type DN2:PERSIST.TXT` blocks on the WB1.3 "Please insert volume DN2"
requester. DN0 remains mounted. This is a DOS/FFS static-handler lifecycle
problem, not a FujiNet mapping failure.

## September 2026 trace findings

The resident command trace isolates the failure to the transition after a
writable secondary volume is ejected.  Immediately after `TD_EJECT`, the
WB1.3 FastFileSystem handler issues `CMD_CLEAR` and then a buffered
`CMD_WRITE`; the write returns `TDERR_DiskChanged` (29).  The handler then
reports the volume read/write-error requester.  This is why mapping the same
catalogue slot again cannot restore it: the later map succeeds at the device
layer, but the handler has already entered its error path.

Clearing the trace after the eject and collecting it immediately after the
next `FMOUNT` shows only the private catalogue-mount request.  In particular,
the DN2 handler issues no new trackdisk request to inspect or accept the
inserted medium.  The Amiberry task snapshot agrees: DN2 has received its
legacy change signal (`0x100`) but is waiting on its packet-port signal.

Two plausible recovery attempts are ruled out:

- Sending `ACTION_FLUSH` through `DeviceProc("DN2:")` before `TD_EJECT` is
  not supported safely by this WB1.3 FFS: it leaves the guest at the
  "Software error - task held" requester before the eject.
- Running the stock `DiskChange DN2:` after the next `FMOUNT` still produces
  the FFS read/write-error requester.
- `Inhibit(DN2:, TRUE)` before the eject is also unsafe: it leaves the guest
  at the "Software error - task held" requester, as does `ACTION_FLUSH`.

The next investigation must therefore find a WB1.3-safe way to make FFS
commit writable metadata before the removable-media transition, or establish
that the classic FFS handler cannot support writable secondary removable
media while another static handler remains live.

## Resolution candidate: native write-back quiescence

The boundary matrix shows that this is not a multi-unit limitation:

- DN2 read-only eject/reinsert succeeds while DN0 remains mounted.
- DN2 writable eject/reinsert fails even when DN2 is the only mounted FujiNet
  unit.

An earlier controlled run inserted `Wait 5` between `Copy` and `FUMOUNT`.
The HDF evidence shows the persisted file after remount and successful final
ejects.  The shell timestamps place the initial eject about seven seconds
after `Copy`, compared with the immediate failure path.  This establishes
that WB1.3 FFS's normal delayed write-back—not concurrent handlers—is the
missing transition.

`FUMOUNT` now performs the same five-second WB1.3-only quiescence internally
before `TD_EJECT`.  The isolated writable DN2 lifecycle and the original
concurrent DN0/DN2 lifecycle both complete through persisted-file readback
and completion-marker emission with that change.  Later Kickstarts keep their
existing handler-retirement lifecycle and do not take this delay.

## Eight static MountList units

The `wb13-a500` acceptance environment successfully starts `DN0:` through
`DN7:`, maps read-only DD media to every unit, and reads `KNOWN.TXT` from each
one.  This proves the shipped static MountList supplies all eight independently
addressable DiskDevice units.

A deliberately diagnostic batch of eight sequential `FUMOUNT` commands
ejected DN0 and DN1, then stalled while beginning DN2's transition.  It is not
part of the normal acceptance case: the established workflows already prove
independent eject/reinsert for DN0 and DN2, including writable DN2 beside live
DN0.  Treat the bulk-eject sequence as a separate WB1.3 resource/lifecycle
investigation; do not infer a limitation in mounting or reading all eight
units from it.

## Read-only media verification

Automated WB1.3 coverage verifies a catalogue `RO` mount through the device's
`TD_PROTSTATUS` result (`protected=1`) and reads its known file.  A manual
`Delete DN0:KNOWN.TXT` reaches the expected WB1.3 "Volume NIOADF is write
protected" requester.  That requester is modal, so the guest test does not
attempt to automate a Cancel click merely to obtain a shell return code.

## Rejected paths

- Standalone `DEVS:DNn` files are not a WB1.3 replacement for its shared
  `DEVS:MountList`; they either fail parsing or interact badly with
  `BindDrivers`.
- Letting the test image preinstall `DEVS:DN0` through `DEVS:DN7` causes
  empty handlers to be started before `FMOUNT`; do not do this for WB1.3.
- Repeating the map after `Mount`, delaying that repeat, lowering the static
  stack to 4000 bytes, and adding `GlobVec = -1` to secondary entries did not
  cure the DN2 remount failure.

## Current design direction

WB1.3 must use one shared MountList augmented with static `DN0:`--`DN7:`
entries. The installer/startup setup should load the resident disk device and
then start those static handlers before `FMOUNT` is used. Independent
eject/reinsert of a secondary active unit is established; a bulk-eject stress
case remains to be understood separately.
