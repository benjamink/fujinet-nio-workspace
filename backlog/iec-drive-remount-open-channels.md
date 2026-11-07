# IEC drive: open channels survive a disk remount

Status: `TODO`

## Goal

Make `IecDriveFrontend` (`repos/fujinet-nio`) stop serving a file or listing
from the previous disk when its `DiskService` slot is remounted while a data
channel is open. Found in the review of fujinet-nio PR #27 (C64 IEC) and left
out of the follow-up commit `264bf2c1`.

## Context

- `IecDriveFrontend::OpenChannel` keeps a `CbmVolume` and a `CbmFileReader`
  that read sectors through `DiskService::read_sector(slot, ...)` on every
  call. Nothing tells the frontend the slot's media changed, so after a
  remount an open streaming channel reads the new image at the old
  track/sector chain. The result is garbage bytes or `66,ILLEGAL TRACK OR
  SECTOR`, with no sign that the disk changed. A listing (`$` on channel 0) is
  copied into memory at OPEN and is not affected.
- A real 1541 misbehaves too if the disk is swapped mid-read, so this is an
  edge case, not a regression. The usual trigger is the config app (F1) or
  `FMOUNT` remounting a slot while a program still has a channel open.
- `src/lib/iec_drive_frontend.cpp`: `close_all()` already exists and is what
  `bus_reset()` and `CLOSE 15` use.

## Work

- [ ] Find out whether `DiskService` has, or can cheaply expose, a per-slot
      mount generation (or the `changed` flag behind `clear_changed()`).
      Prefer that over a callback so `DiskService` stays unaware of the IEC
      layer.
- [ ] In `IecDriveFrontend`, record the generation when a channel opens. On
      the next `send()`, `open()` or status read, if it differs, close the
      stale channels and set a status (`74,DRIVE NOT READY` or the 1541's
      `21,READ ERROR` are candidates; pick one and document it in
      `docs/iec/drive.md`).
- [ ] Tests in `tests/test_iec_drive_frontend.cpp`: remount mid-file ends the
      stream with that status and does not return the new disk's bytes;
      remount with no channel open changes nothing; the new disk's directory
      and files read normally afterwards.

## Acceptance

- A remount with a channel open cannot yield bytes from the other image.
- `DiskService` gains no dependency on the IEC code.
- `c64-netiec-debug` ctest passes.
