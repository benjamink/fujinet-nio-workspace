---
title: 'Complete Pico 2 W platform backends in backlog order'
type: feature
created: '2026-11-15'
status: done
baseline_commit: b2261be69bab1fcd12e9ea47278991c4bae229c0
review_loop_iteration: 1
context:
  - /home/markf/dev/nio/fujinet-nio-workspace/AGENTS.md
  - /home/markf/dev/nio/fujinet-nio-workspace/docs/agent-test-policy.md
  - /home/markf/dev/nio/fujinet-nio-workspace/backlog/pico2w-port.md
  - /home/markf/dev/nio/fujinet-nio-workspace/repos/fujinet-nio/AGENTS.md
---

<frozen-after-approval reason="User authorized executing the backlog in order">

## Intent

Replace the Pico 2 W platform skeleton's backend stubs with working TCP/UDP/DNS,
USB transport and console, flash storage, and TLS/HTTP implementations, in the
order and commit boundaries specified by backlog/pico2w-port.md. Keep measurements
honest: no hardware has been confirmed attached. Build verification and native
logic tests are authorized now; physical acceptance and TLS runtime peak memory
remain explicitly pending hardware.

## Boundaries & Constraints

Always work in repos/fujinet-nio on rp2350-pico2w-platform-skeleton. Keep platform
code in src/platform/pico with no platform ifdefs in shared code. Commit each
backlog item separately, plus the explicitly requested UDP portability commit.
Use external build directories under /tmp. Source workspace scripts/env.sh before
builds. Preserve all existing changes; implementation owns only the files needed
for this port. You are not alone in the workspace; accommodate others' edits.
Do not push, change submodule pins, add coauthor/session trailers, change wire
values, or claim hardware results. Ask before any necessary protocol change.
Do not implement optional WifiBackendKind changes. Implement optional work only
after required items, without compromising verification. Never run the ARM ELF.

## I/O & Edge-Case Matrix

| Scenario | State | Expected behavior | Error handling |
|---|---|---|---|
| Socket buffering | wrap, full, EOF, reuse | ordered bytes, bounded storage, safe handles | backpressure and native errno |
| UDP receive | empty, oversized, queued datagrams | preserve packet boundaries, discard truncated remainder | no buffer overwrite |
| DNS lifecycle | cached, async, failure, timeout | valid opaque address lifetime | late callback cannot access freed state |
| USB | data, disconnect, full TX | FujiBus channel and console isolated | bounded nonblocking progress |
| Flash | blank, valid, corrupt, boundary writes | persistent files, bounded partition access | never format nonblank corruption silently |
| TLS | trusted, invalid, wrong hostname | verify chain and hostname | fail closed |
| HTTP | lengths, chunking, EOF, malformed | conform to existing network API | bounded parsing and errors |

</frozen-after-approval>

## Code Map

- `repos/fujinet-nio/include/fujinet/net/{tcp,udp}_socket_ops.h`: opaque AddrInfo,
  sockaddr pointers, native error classification; implement raw lwIP underneath.
- `src/platform/pico/socket_ops_unavailable.cpp`: replace all ENOSYS methods.
- `src/lib/udp_channel.cpp` and its header: remove BSD address storage/family
  dependency as separate portable change; preserve POSIX/ESP32 behavior.
- `src/platform/pico/{fs_factory,network_registry,channel_factory}.cpp`: registration
  points. TNFS TCP/UDP factory patterns exist in ESP32 fs_factory.cpp.
- `src/app/main_pico.cpp`: already sets up transports when channel exists; add
  console and USB servicing in cooperative loop.
- `src/app/console_{engine,commands,parse,fs_shell}.cpp`: explicitly add to Pico
  build; implement IConsoleTransport and step the console.
- `third_party/esp/esp_littlefs/src/littlefs`: portable vendored LittleFS 2.11;
  reuse directly, avoid ESP VFS wrapper; document in THIRD_PARTY.md.
- `include/fujinet/fs/filesystem.h`: filesystem contract and default listing.
- `pico2w/CMakeLists.txt`, `lwipopts.h`, `mbedtls_config.h`: isolated SDK target.
- SDK `/usr/share/pico-sdk`: raw lwIP, pico_flash, pico_rand and pico_lwip_mbedtls
  available. ALTCP TLS requires explicit hostname. SDK HTTP only implements GET;
  existing API methods and response metadata require a proper HTTP adapter.
- `include/fujinet/net/https_trust_config.h`: existing trust modes; preserve them.
- `pico2w/README.md`: baseline and stub table, update per item with exact sizes.

## Tasks & Acceptance

- [x] Remove UDP platform dependency, test POSIX/ESP32, commit separately.
- [x] Implement host-testable bounded socket state and raw TCP/UDP/DNS; enable
  UDP channel, TNFS factory and tcp registration, tune lwIP with rationale.
- [x] Implement TinyUSB FujiBus CDC and console. Choose isolated CDC interfaces
  or UART stdio/console and document ownership. Commit item 2 after item 1.
- [x] Implement LittleFS flash filesystem with flash_safe_execute; reserve and
  enforce a partition, test boundaries and failure policy. Commit item 3.
- [x] Try ALTCP TLS first; implement TRNG entropy and trust checking, TLS plus
  HTTP/HTTPS registration with API-compatible bounded HTTP behavior. Commit item 4.
- [x] Measure flash/static RAM and linker-map component totals after each item;
  document missing runtime TLS heap/stack measurements and hardware acceptance.
- [x] Run focused behavior tests for extracted logic and required build matrix;
  inspect generated source lists then restore both generated files. Clean status.

Given a Pico SDK installation, when configured and linked, the firmware produces
ELF/UF2 and size reports. Given each matrix scenario, native tests cover the
extracted logic or mocked platform boundary; actual USB/radio/flash/TLS acceptance
is reported separately as untested until hardware is available.

## Spec Change Log

- Final review: raw TCP windows must hold a complete encrypted TLS record;
  increased to 20 KiB with four bounded raw handles. Added callback receive-credit,
  FIFO accept, long-uptime clock, USB lifecycle and HTTP retry/redirect coverage.
  Kept raw lwIP, flash blank-only formatting, certificate verification and explicit
  runtime-memory caveats. Removed copied Unix/Apple guards from Pico time code
  at the user’s request; direct newlib reentrant calls pass native clock tests.
- User confirmed no board attached and requested completion of build-only
  verification. Live TLS heap/stack and physical acceptance remain pending.

## Design Notes

Use raw lwIP and bounded buffers rather than adding FreeRTOS. Guard raw API access
with cyw43_arch_lwip_begin/end, including callbacks' state interactions. Allocate
no unbounded packet queues. Account for callback lifetime after close and DNS
timeout. TLS callbacks affect background stack; static size is only a lower bound.
Prefer UART stdio/console plus one owned CDC for FujiBus unless two CDC interfaces
are simpler to integrate correctly. Flash callbacks copy program input into RAM
and reject out-of-partition accesses. Do not erase corrupt existing storage.

## Verification

- `source scripts/env.sh && cmake -S repos/fujinet-nio/pico2w -B /tmp/nio-pico2w-build -DPICO_BOARD=pico2_w -DPICO_PLATFORM=rp2350-arm-s`
- `source scripts/env.sh && cmake --build /tmp/nio-pico2w-build -j8`
- Native doctest tests for extracted socket, USB buffering, flash boundary and HTTP
  logic; select exact target/tests after inspecting tests/CMakeLists.txt.
- POSIX fujibus-pty-debug equivalent configured outside repository plus ctest;
  inspect build.sh/presets to retain flags while honoring external-build rule.
- ESP32 `./build.sh -b` equivalent external build if toolchain available; record
  exact unavailable toolchain if absent, as the backlog permits.
- `scripts/update_cmake_sources.py`: inspect Pico source exclusion and restore
  CMakeLists_posix.cmake and CMakeLists.txt generated changes, preserving prior edits.
- `git diff --check`, `git status --short`, and `pgrep -x` for launched build tools.

Parent baseline configure completed in /tmp/nio-pico2w-build; baseline build log
is /tmp/nio-pico2w-baseline.log. No hardware tests or runtime peaks obtained.

## Verification Results

Pico firmware and configured ESP32 S3 firmware link; external POSIX CTest passes
all six targets. Native suites exercise actual LittleFS, actual SDK mbedTLS
certificate verification, entropy and Pico time, raw socket callbacks, ALTCP
adapter callbacks in three trust modes, HTTP streaming and measurement parsing.
Raw socket and actual LittleFS suites also passed ASan/UBSan outside the sandbox
(the sandbox prevents LeakSanitizer process inspection).

Reproduction from the repository after sourcing workspace scripts/env.sh:

- `cmake -S pico2w -B /tmp/nio-pico2w-build -DPICO_BOARD=pico2_w -DPICO_PLATFORM=rp2350-arm-s`
- `cmake --build /tmp/nio-pico2w-build -j8`
- `ctest --test-dir /tmp/nio-pico2w-posix --output-on-failure`
- `cmake -S tests/pico -B /tmp/nio-pico-raw-tests` then build and CTest there.
- `cmake -S tests/pico-http -B /tmp/nio-pico-http-tests` then build and CTest there.
- `cmake -S tests/pico-tls -B /tmp/nio-pico-tls-tests` then build and CTest there.
- `cmake -S tests/pico-tls-adapter -B /tmp/nio-pico-tls-adapter-tests` then build and CTest there.
- `PLATFORMIO_BUILD_DIR=/tmp/nio-pico2w-esp32 PLATFORMIO_CACHE_DIR=/tmp/nio-pio-cache pio run`

The existing POSIX disk subprocess test timed out under concurrent compilation;
its focused retry and the complete idle-toolchain suite passed. Generated source
lists were inspected and restored. No wire values, submodule pins or URLs changed.
Optional item 6 remains deferred. No firmware was executed on host or hardware.

## Suggested Review Order

- Start with platform scope, limits and build-only measurement evidence.
  [README.md:1](../../repos/fujinet-nio/pico2w/README.md#L1)
- Follow raw socket ownership, callbacks and DNS timeout lifetimes.
  [socket_ops_raw.cpp:1](../../repos/fujinet-nio/src/platform/pico/socket_ops_raw.cpp#L1)
- Inspect TLS certificate policy and receive-credit handling.
  [tls_protocol.cpp:1](../../repos/fujinet-nio/src/platform/pico/tls_protocol.cpp#L1)
- Check bounded HTTP framing, upload replay and redirects.
  [http_protocol.cpp:1](../../repos/fujinet-nio/src/platform/pico/http_protocol.cpp#L1)
- Inspect flash partition bounds and non-destructive mount failures.
  [littlefs_volume.cpp:1](../../repos/fujinet-nio/src/platform/pico/littlefs_volume.cpp#L1)
- Check USB session ownership and console integration.
  [channel_factory.cpp:1](../../repos/fujinet-nio/src/platform/pico/channel_factory.cpp#L1)
- Review native boundary tests and allocation accounting.
  [CMakeLists.txt:1](../../repos/fujinet-nio/tests/pico/CMakeLists.txt#L1)
  [size_report.py:1](../../repos/fujinet-nio/pico2w/size_report.py#L1)

Final firmware commit: `6870e8017a24059042e866276fff5a547136415b`.
Final measured flash: 1,153,112 bytes; static RAM: 222,312 bytes; reserved
stack: 16,384 bytes. This excludes runtime heap and does not prove live TLS fit.
Final review fixes pass focused gates; firmware repository clean, nothing pushed.
