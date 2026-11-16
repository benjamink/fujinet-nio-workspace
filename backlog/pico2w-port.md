# Pico 2 W (RP2350) port of NIO: remaining work

Goal: run NIO on a Raspberry Pi Pico 2 W (RP2350, Cortex-M33, CYW43439 Wi-Fi, 520 KB SRAM, 4 MB flash)
by replacing the stubs in the skeleton with real backends.

## Starting point

- Repo `repos/fujinet-nio`, branch `rp2350-pico2w-platform-skeleton` (local, not pushed). Work on it or
  branch from it. The maintainer pushes and opens PRs: do not push or run `gh` write actions.
- Read first: `repos/fujinet-nio/pico2w/README.md` (what is real, what is stubbed, what is excluded and
  why, baseline size), then `repos/fujinet-nio/AGENTS.md`, `docs/architecture.md`, and
  `docs/agent-test-policy.md`.
- The hardware (a genuine Pico 2 W) arrives after this was written. Until the maintainer says a board is
  attached, everything is build-verified only; say so in commits and in your report.

## Rules

- No platform `#ifdef` in `src/lib` or shared code; platform code lives in `src/platform/pico/`.
- Commit locally, one commit per item below, message says what changed and how it was verified.
  **No `Co-Authored-By` trailer**, no agent or session mentions. Never push.
- Do not mention `mozzwald/fujinet-palm`. No wire-protocol changes (stop and ask if one seems needed).
- Do not keep the output of `scripts/update_cmake_sources.py` (it rewrites hand-maintained parts); run it
  only to confirm no Pico source leaked into the generated lists, then `git checkout --` the two files.
- Build outside the repos (scratchpad or `/tmp`) and confirm `git status` is clean afterwards.
  No stray processes (`pgrep -x`). New third-party code goes in `THIRD_PARTY.md`.

## Build

```sh
source scripts/env.sh                 # exports PICO_SDK_PATH (AUR pico-sdk 2.3.1: lwIP, mbedTLS, CYW43, TinyUSB)
cd repos/fujinet-nio
cmake -S pico2w -B <scratch>/pico2w-build -DPICO_BOARD=pico2_w -DPICO_PLATFORM=rp2350-arm-s
cmake --build <scratch>/pico2w-build -j8      # prints arm-none-eabi-size at the end
```

Baseline: 835 KB flash, 61 KB static RAM (`-Os`, gc-sections). Never run the built ELF
(the host has `qemu-arm` binfmt; it segfaults).

Things already learned, in `pico2w/CMakeLists.txt` and its comments: exceptions and RTTI are forced on
with `PICO_CXX_ENABLE_*`; `CMAKE_CXX_EXTENSIONS` stays ON; newlib has no gthreads, hence
`pico2w/compat/`; lwIP is `NO_SYS=1` raw API, so wrap lwIP calls in `cyw43_arch_lwip_begin/end`;
`mbedtls_hardware_poll()` is unimplemented and only links because nothing uses TLS yet.

## Work items, in order

1. **Sockets (TCP, UDP, DNS).** Replace `src/platform/pico/socket_ops_unavailable.cpp` with
   `net::ITcpSocketOps` / `IUdpSocketOps` (`include/fujinet/net/`) on lwIP raw pcbs. Suggested: an fd table
   with per-socket receive ring buffer, lwIP callbacks filling it, `dns_gethostbyname` behind the opaque
   `AddrInfo`. Keep ring-buffer and fd-table logic free of lwIP types so it is host-testable. Then
   re-enable `src/lib/udp_channel.cpp` (fix its `<sys/socket.h>` dependency as its own commit, with POSIX
   and ESP32 still compiling), give `fs_factory.cpp` a real TNFS client factory, and register the real
   `tcp` protocol in `network_registry.cpp`. Tune `pico2w/lwipopts.h` and say why. FreeRTOS + lwIP sockets
   is acceptable only if justified with the size delta. Reference: `src/platform/esp32/tcp_socket_ops_espidf.cpp`.
2. **USB CDC channel and console.** TinyUSB CDC `io::Channel` returned by `channel_factory.cpp`, wired
   through `core::setup_transports`; a console transport. `pico_stdio_usb` is on and will conflict:
   decide second CDC interface vs stdio on UART, and document it. Reference: `src/platform/esp32/usb_cdc_channel.cpp`.
3. **Flash filesystem.** LittleFS on a reserved region of the 4 MB flash, registered as `flash` (the config
   store reads `fujinet.yaml` from it). Use `flash_safe_execute`; document partition layout and wear.
   Reference: `src/platform/esp32/fs_factory.cpp`.
4. **TLS and HTTP.** mbedTLS through `pico_mbedtls` (try lwIP `altcp_tls` first), `mbedtls_hardware_poll()`
   from the TRNG, trust roots as in `include/fujinet/net/https_trust_config.h`. Register `tls`, `http`,
   `https`. Measure the RAM cost of one TLS connection.
5. **Measurement.** After each item rerun the size report with the per-component breakdown from the linker
   map (method in the README), record peak heap and stack with a TLS connection open, and update the
   README table and its "lower bound" caveats. This answers whether NIO with TLS fits in 520 KB.
6. **If time allows:** UART channel, Wi-Fi scan and BSSID select, SNTP, `memory_stats` low-water mark,
   a core-1 `service_task`. A Pico `WifiBackendKind` changes a wire value: ask first.

## Verification

Per `docs/agent-test-policy.md`: always link the Pico build and record the size. Host doctest tests
(`tests/test_*.cpp`, `./build.sh -cp fujibus-pty-debug`, `ctest --test-dir build/fujibus-pty-debug`) for
extracted pure logic. If `src/lib` or shared headers change, also build the POSIX preset and the ESP32
build (`./build.sh -b`) if its toolchain is present, and say so if not. Update the README table per item.

## Final report

Per item what changed, new flash and RAM numbers, measured heap and stack if obtained, what is untested
on hardware, and decisions for the maintainer to review (lwIP raw vs FreeRTOS, USB layout, flash layout,
trust roots). Do not claim hardware behaviour you did not observe.
