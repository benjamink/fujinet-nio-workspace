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
then start those static handlers before `FMOUNT` is used. The remaining work
is to make independent eject/reinsert of a secondary active unit reliable.
