# FujiNet default disk for Amiga

The FujiNet default disk is a normal ADF that the device exposes on disk unit
zero when startup did not recover a user-selected image for that unit.  It is
not an Amiga system boot disk: Workbench still boots from the user's normal
floppy or hard disk.  Its purpose is to make a useful FujiNet volume appear as
`DN0:` after the resident drivers have loaded.

The supplied images contain `config-nio` and the standard `F*` utilities.  All
of them are FFS, double-density ADFs (880 KiB).  That fixed type makes the
image safe for the WB1.3 static `DN0:` endpoint and for a WB3.1 handler that
cannot be retired and rebuilt with another filesystem or geometry.

## Build and package

Build one profile explicitly:

```sh
./scripts/build.sh amiga-default-disk-wb13
./scripts/build.sh amiga-default-disk-wb31
./scripts/build.sh amiga-default-disk-wb32
```

`./scripts/build.sh boot-disks` builds all three alongside the Atari,
MS-DOS, and BBC images.  Outputs are copied to both firmware asset trees:

```text
repos/fujinet-nio/distfiles/boot/amiga/<profile>/FujiNet-Default-WB*.adf
repos/fujinet-nio/distfiles/esp32-data/boot/amiga/<profile>/FujiNet-Default-WB*.adf
```

The latter is included when the ESP32 storage partition is flashed.

## Configure FujiNet

Select the image matching the Workbench artifact profile.  On an ESP32
FujiNet, for example:

```yaml
boot:
  mode: config
  config_uri: "flash:/boot/amiga/wb13/FujiNet-Default-WB13.adf"
  readonly: true
```

For a POSIX/debug device use `persist:` instead of `flash:`:

```yaml
boot:
  mode: config
  config_uri: "persist:/boot/amiga/wb32/FujiNet-Default-WB32.adf"
  readonly: true
```

At device startup, runtime disk recovery takes precedence.  If it recovered a
user disk for unit zero, FujiNet leaves that disk in place.  Otherwise it
prepares the configured default ADF for unit zero.

## Activate it from Workbench

Install the matching resident devices and command binaries in the usual way,
then put this after the resident-device load lines in the hard-disk startup
sequence:

```text
C:FBOOT
```

`FBOOT` asks FujiNet to restore the configured default image, validates that
it is the supported FFS/DD ADF, then makes it visible as `DN0:`:

- WB3.1/WB3.2: creates the normal dynamic `DN0:` handler when no handler is
  present, or starts a previously inactive one.
- WB1.3: starts the installed static `DN0:` MountList endpoint.

`FBOOT` deliberately refuses to replace an active WB2+ `DN0:` handler.  That
protects a user disk from an accidental manual `FBOOT`; at cold startup there
is no active handler, so the configured default attaches normally.

On WB3.1, a handler that the OS cannot retire remains tied to its initial
filesystem and geometry.  Since the default image is permanently FFS/DD, it
can safely refill that `DN0:` endpoint.  WB3.2 has the fuller dynamic
eject/removal lifecycle.

Once mounted, open `DN0:config-nio` from Workbench.  The standard installer
places `fmount` and `fumount` in `C:`, so config-nio resolves them through the
normal inherited AmigaDOS command path.  Advanced installations may instead
set its `FMOUNT=` and `FUMOUNT=` ToolTypes explicitly.

