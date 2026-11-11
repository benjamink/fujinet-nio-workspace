# One Amiga media-fit decision for FMOUNT and config-nio

Status: `TODO`

## Goal

"Can this drive take this image, and what will its handler do?" is decided in one place,
in the driver, and both `FMOUNT` and config-nio call it. Neither carries its own copy of
the media rules or of the Workbench version knowledge.

## Context

Review of `nio-config#7` found the same rules written twice:

| Rule | `FMOUNT` (`nio-core-apps`) | config-nio (`nio-config`) |
|---|---|---|
| Image class: 1760 blocks DD, 3520 HD, 512-byte sectors | `fujinet_disk_classify_media_profile` (driver, `fujinet-amiga-disk/support.h`) | `amiga_media_classify` |
| Filesystem: `DOS\0` OFS, `DOS\1` FFS | `fujinet_disk_classify_filesystem` (same header) | `amiga_media_classify` |
| A started handler's media (`bpt > 11` is HD, `dostype & 1` is FFS) | `node_snapshot` / `refuse_media_change` | `handler_pinned` |
| Does the handler stay fixed to its media? | tries `ACTION_DIE` and reads `ERROR_ACTION_NOT_KNOWN` | `amiga_handler_pins_media`: dos.library 40 only (WB3.1) |
| Which `FMOUNT` build is installed | prints a usage line | config-nio matches "HN0:" / "DN0:" in it |

The last two are the weak points. `FMOUNT` learns whether a handler can retire by sending
`ACTION_DIE`, which kills a live handler, so config-nio cannot do the same and uses the
Workbench version. That was wrong for WB3.2 until `nio-config#7` was amended; WB3.1.4 (dos 46)
is assumed to retire handlers and is untested. And the flavour check couples two repositories
through a message string.

## Work

- [ ] In `fujinet-nio-driver`'s public `fujinet-amiga-disk` API, add a pure-C function for the
      decision (media profile and DosType of the image, the unit's kick13 endpoint or its
      handler's DosEnvec, the Workbench version) returning fits, wrong density, or wrong
      filesystem, plus the version rule for "this handler stays fixed". It must not touch
      the OS or the device, so it has host tests like the classifiers.
- [ ] `FMOUNT` calls it for its refusal, keeping its `ACTION_DIE` probe for the real retire.
- [ ] config-nio drops `amiga_media_classify`, `amiga_drive_fit`, `amiga_handler_pins_media` and
      the duplicated `bpt` / `dostype` reading, and builds the driver's sources as
      `nio-core-apps` does (`FUJINET_NIO_DRIVER_BUILD`).
- [ ] Replace the `FMOUNT` usage-line match with a query in the same API (for example, which
      build of the tools is installed), so no repository parses another's message text.
- [ ] Check WB3.1.4 (dos 46) with an Amiberry run and record the result next to the rule.

## Dependencies

`nio-config#7` and `#8` merged first. Owning repositories: `fujinet-nio-driver` (the function),
`nio-core-apps` (`FMOUNT`), `nio-config` (the caller).

## Acceptance

- [ ] The media and handler rules exist once, with host tests in the driver.
- [ ] `FMOUNT` and config-nio refuse and accept the same drive and image combinations on wb13,
      wb31 and wb32 (Amiberry), including a started handler of another type on WB3.1 and on WB3.2.
- [ ] No source in `nio-config` or `nio-core-apps` matches text printed by the other.
