# Atari compact launcher: why its link order matters

Status: `TODO`

Start this straight after `nio-config` PR #6 (the C64 launcher) is accepted.

## Goal

Find out why the Atari `config-nio` only passes its boot tests when its assembly is linked in the
order it always has been, fix the cause, and then delete the explicit order so the Atari builds
from the directory like the C64 does.

## Context

- `repos/nio-config/makefiles/build.mk` sets `CONFIG_NIO_ASM_SRCS` for the Atari by hand:
  `atari_basicoff.s`, `compact_compose.s`, `atari_dli.s`, `atari_scr_fast.s`, `compact_view.s`. The
  directory order puts `compact_view.s` first.
- In directory order the build links and `tests/atari` (the fast suite, 32 tests) passes, but three
  of the boot tests (`NIO_ATARI_BOOT=1`, `test_boot.py`) fail by timeout, reproducibly in a clean
  environment: `test_mount_screen_and_error_restore`,
  `test_option_boots_an_assigned_boot_disk` and
  `test_option_boots_an_assigned_xex_through_the_wrapper`. In the original order they pass in
  about 65 seconds. The failing runs take about 350.
- What moves between the two builds (from the linker's label files, `atari-banked`): 28 symbols.
  Everything in `CODE` from `setcursor` onward moves up by 0x165 bytes, and eleven zero-page
  variables change address (`scr_zr`..`scr_zv` from `$90-$97` to `$A1-$A8`, `view_pos`..`view_key`
  from `$9E-$A4` to `$8D-$93`). The segment extents are identical.
- What does not move: the display list (built at the fixed `$0600`), and the screen row tables and
  buffers (`row_bg`, `row_fg`, `lms_lo`, `lms_hi`, `nxt_bg`, `nxt_fg`, `scr_swap`).
- Not yet known whether it is the code moving (page alignment of something that assumes it), the
  zero page moving (something else using those addresses), or both.

## Work

- [ ] Bisect: build the banked Atari with only the zero-page variables moved, then with only the
      code moved (pad `CODE` by 0x165 bytes), and run the three boot tests for each. Use a clean
      environment: a stale `netsiohub` or AltirraSDL holding UDP 9997 makes the tests fail for the
      wrong reason (check with `ss -lnup | grep 9997` first).
- [ ] Look for the dependency the failing variant breaks: page-crossing data tables and branches,
      anything addressed by a fixed number in `atari_dli.s`, `atari_scr_fast.s` and the bank
      switch, and zero-page use by the library's SIO code, the loader and PicoBoot.
- [ ] Check the Atari memory-boundary rules against the layout, in case something now straddles
      one. From `repos/fujinet-config-ng/cfg/atari.full.cfg`: display lists must sit on a 1K
      boundary and must not cross one; player/missile graphics need a 1K-aligned area (this
      launcher does not use them, but a future screen might); screen memory that crosses a 4K
      boundary needs a jump in the display list at it (`atari_scr.c` already nudges row bases
      for the 4K case).
- [ ] Fix the cause so that the layout no longer depends on link order, for example by aligning
      the sensitive routines or tables explicitly, or by giving the zero-page variables fixed
      places in the linker configuration.
- [ ] Remove the explicit `CONFIG_NIO_ASM_SRCS` block from `build.mk` and its comment, and the
      matching paragraph in `repos/nio-config/src/platform/compact/README.md`.

## Acceptance

- `make TARGET=atari`, `make atari-banked` and `make TARGET=c64` build with no explicit link
  order.
- The Atari fast suite and the full boot suite (`NIO_ATARI_BOOT=1`) pass, including the three tests
  above.
- A note in the compact launcher's README says what the dependency was.
