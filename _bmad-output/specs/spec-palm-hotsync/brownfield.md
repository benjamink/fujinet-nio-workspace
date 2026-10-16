# Brownfield notes: Palm OS support

## Prior art (reference only, not to be copied)

| Source | What it is |
|---|---|
| `dillera/fujinet-firmware` branch `palm-demo-fozz`, commits `dc815794d..` | Classic firmware Palm work. `lib/hotsync/` is about 4,050 lines, ported from palm-sync 0.2.1 (Apache-2.0). Also: `lib/device/rs232/rs232HotSync.*`, the hooks in `lib/bus/rs232/rs232.cpp`, `docs/hotsync.md`, `tests/HotSyncTests.cpp` (22 doctest cases from real Palm OS 3.3 captures) and `tools/hotsync-fakepalm/fake_palm.py` |
| FujiNetWIFI/fujinet-firmware PRs | #1824 (expose the bus port): closed, design rejected. #1826 (HotSync stack): open, changes requested (Windows `ws2_32`, palm-sync LICENSE, PSRAM caps, cradle design) |
| `dillera/fujinet-palm` | Palm OS apps (prc-tools, C89). `common/fujibus.c`, `fnlink.c` and `fnnet.c` implement the classic FujiBus client. Apps: FN HotSync (`ADHS`), FN Test (`ADTS`), FN Lobby, FN Bounce World, FN Texas Hold'em, FN FujiPet |
| `palm-sync` (TypeScript, Apache-2.0) | Protocol reference, with recorded test data under `src/tests/testdata` |
| `host-harness/` (also `fujinet-palm/tools/hotsync-harness/`) | macOS serial harness plus traces (`firstlight.trace`, `sync1.trace`) from the real cradle |

### Classic module map to NIO home

| Classic module | Portable? | NIO home |
|---|---|---|
| `Slp`, `PadpTransport` (+CMP), `NetSyncTransport`, `Dlp`, `DlpClient`, `PalmDatabase`, `HotSyncSession`, `Datebook`, `DatebookConduit` | yes (about 3,000 lines; depends only on time helpers) | new `fujinet::hotsync` library in `repos/fujinet-nio` (`include/fujinet/hotsync/`, `src/lib/hotsync/`) |
| `HotSyncLink`, `DlpTransport`, `HotSyncStorage`, `HotSyncCalendar` interfaces | yes | same library, as injected interfaces |
| `HotSyncCradleLink` (settle, WAKEUP deadline), `rs232HotSync` mutex/condvar hand-off, `HotSyncService::poll_serial` windowing | logic yes, glue no | cradle channel adapter, see `cradle-sharing.md` |
| `HotSyncService` (thread, fnTcpServer, core pinning) | no | NIO platform service (task model is an open question) |
| `HotSyncLinks` (fnTcpClient, IOChannel) | no | links over `net::ITcpSocketOps` and the cradle adapter |
| `HotSyncFsStorage` (FileSystem, fnSDFAT) | no | storage over `fs::StorageManager` / `IFileSystem` |
| `HotSyncNetCalendar` (GCAL/ICAL protocols, Google OAuth) | no | ICS fetch over NIO's HTTP network protocol (CAP-6) |
| `fnc_hotsync.cpp` (`[HotSync]` ini) | no | `hotsync:` block in `FujiConfig` YAML |
| web UI panel, `/hotsync-status` | no | diagnostics provider and console command |
| `fujinet-rs232-s3-palm` board, `RS232_NO_HW_FLOW_CONTROL` | no | FN-RS232 S3 env and `uart.flow` config |

## NIO touchpoints (`repos/fujinet-nio`)

| Area | Where |
|---|---|
| Channel contract | `include/fujinet/io/core/channel.h`. Baud is not part of it. |
| ESP32 UART | `include/fujinet/platform/esp32/uart_channel.h:50` `setBaudrate`, `:57` `reconfigure(UartConfig)` (concrete methods only) |
| POSIX serial | `src/platform/posix/serial_channel.cpp`. Supports 9600 to 230400; `FN_SERIAL_PORT`, `FN_SERIAL_BAUD` |
| Channel adapter precedent | `include/fujinet/platform/esp32/atari_sio_fujibus_channel.h`, `src/platform/posix/atari_netsio_fujibus_channel.cpp` |
| Transport selection | `src/lib/bootstrap.cpp:35-95`. `LegacyNetworkAdapter` is installed only for SIO/IWM/IEC. |
| FujiBus reply convention | `src/lib/fujibus_transport.cpp:119-128` (status U8 in `param[0]`) |
| Build profiles | `include/fujinet/build/profile.h`; `src/lib/build_profile/*.cpp` (POSIX); `src/platform/esp32/build_profile.cpp`; RS-232 preset `fujibus-rs232-debug` |
| ESP32 RS-232 envs | `pio-build/ini/platforms/platformio-fujibus-gpio-rs232-*.ini`; pinmap `src/platform/esp32/pinmap.cpp:57-118`; sdkconfig map `pio-build/sdkconfig/00_platform_sdkconfig_map.txt` |
| TCP listen/accept | `include/fujinet/net/tcp_socket_ops.h`; non-blocking listener example in `src/lib/modem_device.cpp` |
| Storage | `include/fujinet/fs/storage_manager.h`. `defaultPersistentFileSystem()` is `host`, then `sd0`, then `flash`. |
| Long work | `include/fujinet/platform/large_stack.h` runs a job and **waits**. There is no long-lived task API; ESP32 `main_esp32.cpp` creates its tasks directly. |
| Services | `docs/architecture.md` §Platform services, §Polling / background work; `docs/event_driven_services.md` (start on `GotIp`) |
| Config | `include/fujinet/config/fuji_config.h`, `fuji_config_yaml_store.cpp` |
| Diagnostics | `include/fujinet/diag/diagnostic_provider.h`; examples `src/lib/diagnostic_modem_provider.cpp`, `diagnostic_uart_channel_provider.cpp` |
| Wire IDs | `include/fujinet/io/protocol/wire_device_ids.h` |
| Tests | doctest `tests/test_*.cpp` (globbed); `docs/agent-test-policy.md` (workspace) |

## Client side (`repos/fujinet-nio-lib`)

- Stream targets supply only a byte channel and share `src/common/fn_transport_stream.c` (`makefiles/targets.mk:48-52`). `msdos-serial` is the closest precedent; Amiga (`amigagcc`, m68k) is the closest CPU and toolchain precedent.
- A Palm target needs:
  - a prc-tools m68k compiler family;
  - a C89-clean subset;
  - a byte channel over the New Serial Manager (`SrmOpen(serPortCradlePort, 115200)`, Palm OS 3.3+);
  - the retry policy in `palm-protocols.md`.
- Must pass `make check` for every touched target.

## Unknowns to resolve in the first story of each phase

- Whether `fujinet-nio-lib`'s C dialect and code size fit Palm's 32 KB code segment limit. FujiPet already uses 28.5 KB of 32 KB with the classic client.
- Whether `IFileSystem` supports the rename and listing that the install queue and backup need.
