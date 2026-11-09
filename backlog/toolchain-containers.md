# Standard containerised toolchains

Status: `TODO`

## Goal

Everyone builds the awkward targets the same way, from the same pinned toolchain, without
depending on another project's repository. Docker is the common ground.

## Context

Reviews of the Palm OS and classic Mac targets showed the gap. Each target's toolchain is
documented differently, and some of the instructions point outside the NIO repositories:

| Target | Toolchain | How it is obtained today |
|---|---|---|
| Palm OS (`fujinet-nio-lib` `palmos-*`, `palmos-shared`; `nio-config` Palm) | prc-tools-remix 2.3.6 (GCC 2.95.3), PilRC, build-prc, Palm OS 3.5 SDK, and for USB the Handspring SDK headers | A Dockerfile in `mozzwald/fujinet-palm`, which is not an NIO repository. `fujinet-nio-lib#9` was asked to add its own pinned Dockerfile and drop the references |
| Classic Mac (`mac68k`, `fujinet-nio-lib#10`) | Retro68 (`m68k-apple-macos-gcc`) | Build it from source, or the prebuilt `ghcr.io/autc04/retro68` image. Verified: `docker run --rm -u $(id -u):$(id -g) -e HOME=/tmp --entrypoint /bin/bash -v "$PWD":/work -w /work ghcr.io/autc04/retro68 -c 'export PATH=/Retro68-build/toolchain/bin:$PATH; make mac68k'` builds with no warnings (image 5.59 GB, GCC 16.1.0) |
| Amiga | amiga-gcc, NDK, clib2 | A local install under `/opt/amiga`, readable headers needed |
| MS-DOS | Open Watcom | A local install under `/opt/watcom` |
| Atari, BBC, C64 | cc65 | Built into `repos/cc65` or installed, through `scripts/env.sh` |

Findings from the reviews that this must respect:

- The AUR `retro68-git` package needs Apple's MPW archive (`MPW_fully_updated.sit`) supplied by hand
  and builds GCC from source. The Retro68 image defaults to the open-source multiversal interfaces
  and needs no Apple files.
- The Handspring SDK (`Include/UsbMgr.h`, from palmdb.net's Palm OS SDK page) has an EULA that
  restricts redistribution. It stays an input the user supplies, never baked into an image or
  committed.
- Running a container as root leaves root-owned files in the tree. `-u $(id -u):$(id -g)` with
  `-e HOME=/tmp` and `--entrypoint /bin/bash` worked for Retro68.
- A worktree outside the workspace layout breaks sibling lookups (`../fujinet-nio`,
  `../fujinet-nio-driver`, `cc65-clib`), so the wrapper must mount what it needs explicitly.

## Work

- [ ] Decide which toolchains move into containers (Palm and Retro68 for certain; Amiga and
      Watcom if the installs are as awkward) and which stay on `scripts/env.sh`.
- [ ] A Dockerfile or pinned image reference per toolchain, owned by an NIO repository, with the
      versions and any source URL fixed (no `master` downloads).
- [ ] One documented `docker run` pattern and a wrapper in `scripts/` that applies it: run as
      the user, entrypoint override, the work directory and sibling repositories mounted, the
      toolchain `PATH`, optional read-only mounts for external SDKs.
- [ ] Tasks in `scripts/build.sh` for the container-built targets, so they build the same way
      as the rest, and the toolchain checks in `scripts/env.sh` say which route is in use.
- [ ] Update each repository's build documentation to give the container route first, and to
      stop referring to another project's repository.
- [ ] Say where the images live (a registry, or built from the Dockerfiles) and how CI gets
      them.
- [ ] `make check` in `fujinet-nio-lib` needs several of these toolchains; make that
      explicit in `docs/agent-test-policy.md` (an unavailable toolchain is an environment
      blocker, not a skip).

## Dependencies

`fujinet-nio-lib#9` (Palm: its own Dockerfile), `fujinet-nio-lib#10` (Mac: documentation of the
Retro68 image), and the build orchestration in `build-orchestration-followups.md`.

## Acceptance

- From a clean checkout, a person with Docker and no other toolchain builds `palmos-shared`
  (given the Handspring SDK directory) and `mac68k` with the documented command.
- No NIO repository documents or depends on `mozzwald/fujinet-palm`.
- The images are pinned: rebuilding next month gives the same compiler.
