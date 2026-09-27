# Amiga artifact profiles

Every distributable Amiga artifact is built for an explicit Workbench profile.
There is no generic release output and no default release ADF.

| Profile | Runtime/CRT | Repository build roots | Staged package | Release manifest |
| --- | --- | --- | --- | --- |
| `wb13` | Workbench/Kickstart 1.3, `nix13` | `repos/*/build/amiga/wb13/` | `build/amiga-artifacts/wb13/NIO/` | `configs/amiga/release-adf-wb13.yaml` |
| `wb31` | Workbench 3.1, `clib2` | `repos/*/build/amiga/wb31/` | `build/amiga-artifacts/wb31/NIO/` | `configs/amiga/release-adf-wb31.yaml` |
| `wb32` | Workbench 3.2, `clib2` | `repos/*/build/amiga/wb32/` | `build/amiga-artifacts/wb32/NIO/` | `configs/amiga/release-adf-wb32.yaml` |

Build and package one profile with:

```sh
scripts/amiga-artifacts wb13
scripts/amiga-artifacts wb31
scripts/amiga-artifacts wb32
```

The script builds the compatible driver and application set from source,
then stages distributable files in the matching `NIO/` directory. Workbench
profiles mount that staged directory as the read-only `NIO:` volume and invoke
the matching build before launch. Consequently a WB1.3 session cannot receive
a WB3.x executable merely because it was built later.

Create an ADF only by naming its target profile:

```sh
scripts/amiga adf release --manifest configs/amiga/release-adf-wb13.yaml
scripts/amiga adf release --manifest configs/amiga/release-adf-wb31.yaml
scripts/amiga adf release --manifest configs/amiga/release-adf-wb32.yaml
```

Outputs are `build/NIORelease-WB13.adf`, `build/NIORelease-WB31.adf`, and
`build/NIORelease-WB32.adf`. Add a new Workbench generation by adding a new
profile to `scripts/amiga-artifacts`, `configs/amiga/workbenches.yaml`, and a
matching `release-adf-<profile>.yaml`; do not introduce an unversioned output.

`wb13` deliberately excludes utilities that require later DOS APIs. Its
package includes `Install-FujiNet-WB13`, whose installation steps are covered
in [Amiberry testing](amiberry-testing.md).
