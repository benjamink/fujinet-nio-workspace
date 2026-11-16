---
title: 'Use both Pico 2 W cores with an isolated USB worker'
type: feature
created: '2026-11-15'
status: done
baseline_commit: 6870e8017a24059042e866276fff5a547136415b
review_loop_iteration: 0
context:
  - /home/markf/dev/nio/fujinet-nio-workspace/AGENTS.md
  - /home/markf/dev/nio/fujinet-nio-workspace/docs/agent-test-policy.md
  - /home/markf/dev/nio/fujinet-nio-workspace/repos/fujinet-nio/AGENTS.md
---

<frozen-after-approval reason="User requested both-core utilization at stock clock">

## Intent

The current Pico port leaves core 1 idle and services USB cooperatively with
potentially blocking network operations. Use both cores at the stock 150 MHz:
core 0 owns NIO, Wi-Fi/lwIP/TLS, filesystem and UART console; core 1 owns USB
initialization, interrupts and servicing. Exchange bytes through bounded queues.
This provides concurrent transport progress, not a claimed doubling of speed.

## Boundaries & Constraints

Always keep Pico code under src/platform/pico and select it through the existing
Pico build. No platform guards in shared code or copied Unix/Apple gates in Pico
code. No FreeRTOS, overclocking, wire changes, generic core-1 service tasks or new
user settings. Core 1 must register flash lockout before core 0 can mount/write
flash. Never assume the second core is safe while it executes XIP code. No FIFO
application messages: SDK lockout owns that resource. User confirmed no hardware;
finish native/build verification and document physical acceptance as pending.
Do not push or change workspace submodule pins. Commit locally with verification.

## I/O & Edge-Case Matrix

| Scenario | Input/state | Expected behavior | Error handling |
|---|---|---|---|
| Concurrent traffic | worker and channel progress independently | ordered bounded RX/TX | no races or cross-core TinyUSB calls |
| RX full | application stops consuming | stop draining CDC; retain bytes | backpressure, no healthy-session loss |
| TX full/short submit | queue capacity exceeded or partial device acceptance | atomic enqueue; preserve unsent bytes | existing overflow quarantine |
| USB session change | disconnect/reconnect/reset during staged I/O | clear old RX/TX and advance epoch | no prior-session response leakage |
| Startup/teardown | worker init failure or channel detached | no stale pointers or flash-before-ready | bounded explicit failure |
| Flash operation | worker executing from flash | lockout participates before erase/program | no unsafe execution if coordination fails |

</frozen-after-approval>

## Code Map

- `repos/fujinet-nio/src/app/main_pico.cpp`: currently calls init_usb before CYW43
  initialization and pumps USB before/after core.tick. Replace with checked worker
  startup before filesystem initialization; all application objects remain core 0.
- `src/platform/pico/channel_factory.cpp`: current raw global UsbChannel pointer
  and direct TinyUSB access must become stable synchronized shared state. TinyUSB
  calls belong only to worker core; Channel methods access only bounded queues.
- `include/fujinet/platform/pico/usb_service.h`: expose worker startup, not a
  foreground pump; keep UART console service separate.
- `src/platform/pico/detail/{usb_tx,socket_state}.h`: existing bounded rings,
  overflow quarantine and connection epoch semantics to preserve/extend.
- `src/platform/pico/flash_filesystem.cpp`: already uses flash_safe_execute;
  startup must establish its multicore precondition.
- `pico2w/CMakeLists.txt`: link pico_multicore, remove CORE1_SAFE assertion,
  explicitly size core1 stack. Default inherits 16 KiB, larger than scratch-X.
- SDK `pico_multicore`, `pico_flash`, TinyUSB dcd_rp2040: lockout victim registration,
  launch and USB IRQ initialization APIs. Core1 can use a 4 KiB scratch-X stack
  initially, map-checked and runtime high-water explicitly pending.
- `tests/pico/`: existing boundary mocks and standalone CMake harness; add focused
  native dual-core bridge and worker ownership/lifecycle tests.
- `pico2w/{README.md,size_report.py,measurements/}`: report both stack reservations
  and updated static footprint. Preserve earlier historical measurements.

## Tasks & Acceptance

- [x] Correct the proven TLS pool sizing failure in pico2w/lwipopts.h, add actual
  SDK allocator tests, document/re-measure and commit this prerequisite separately.
- [x] Add a bounded synchronized USB bridge and exclusive core1 worker, with
  explicit attachment/lifetime and staged-I/O epoch handling.
- [x] Integrate checked boot readiness before flash initialization; remove
  foreground TinyUSB service and unsafe flash assumption; allocate/map both stacks.
- [x] Add native tests covering every matrix row, including actual production
  adapter mock calls and two-thread bridge stress where practical.
- [x] Build Pico, run focused native gates and regenerate measurement report;
  inspect generated source lists and restore incidental rewrites.
- [x] Document fixed core assignment, flash pause behavior, bounded queues, no
  measured speedup, and pending hardware latency/stack acceptance. Commit locally.

Given a blocked core0 network operation, when core1 runs, USB servicing progresses
without calling NIO or network code from core1. Given a full RX queue, when the
worker pumps, it leaves excess data in CDC for USB backpressure. Given startup
failure, when main receives it, flash mounting cannot proceed. Given a reconnect,
when application reads/writes resume, old-session buffers are unavailable.

## Spec Change Log

- Investigation proved an existing TLS allocation failure: SDK ALTCP replaces
  mbedTLS allocation with lwIP's 24 KiB heap, but even one default 16 KiB-record
  SSL context cannot allocate both record buffers. Scratch actual-SDK probe at
  /tmp/nio-tls-heap-probe proves 24 KiB fails, 64 KiB only fits one context, and
  96/128 KiB fit two bare contexts (host-sized allocations, not hardware peaks).
  Fix the bounded TLS pool as a separate prerequisite commit: initially 128 KiB
  with regression testing through actual SDK allocator plus certificate parsing
  and two setup contexts; retain explicit handshake/runtime memory caveats.

## Design Notes

Prefer one fixed I/O worker over an RTOS conversion. Guard all shared queue,
epoch, fault and attachment state; no lock across tud_task, flash, waits, logging,
or application callbacks. No C++ allocation/logging/network on core1. Initialize
TinyUSB on its owning core, not just its polling loop. Use semaphore or atomic
startup state instead of intercore FIFO. Keep foreground locks very short and
check lock ordering against SDK flash lockout and interrupt contexts.

The implementer owns this feature's firmware, tests and docs. Other work may be
present; do not revert others' edits. Parent may supply additional verified SDK
findings. Do not recursively launch the build workflow; this is its implementation
handoff. Existing TLS and HTTP boundaries remain core0-owned.

## Verification

Source workspace scripts/env.sh before each build/test. Use external directories.

- `cmake -S repos/fujinet-nio/pico2w -B /tmp/nio-pico2w-build -DPICO_BOARD=pico2_w -DPICO_PLATFORM=rp2350-arm-s`
- `cmake --build /tmp/nio-pico2w-build -j8` — link ELF/UF2, never execute ARM ELF.
- `cmake -S repos/fujinet-nio/tests/pico -B /tmp/nio-pico-raw-tests` then
  `cmake --build /tmp/nio-pico-raw-tests -j4` and
  `ctest --test-dir /tmp/nio-pico-raw-tests --output-on-failure`.
- Native production worker: `cmake -S repos/fujinet-nio/tests/pico -B /tmp/nio-dualcore-native`,
  `cmake --build /tmp/nio-dualcore-native -j4`, then
  `ctest --test-dir /tmp/nio-dualcore-native --output-on-failure` — 6/6 passed:
  raw/flash plus lifecycle, flash registration failure, USB init failure, timeout.
  The actual worker/channel code is compiled against minimal SDK/TinyUSB fakes.
- Concurrent bridge: `cmake -S repos/fujinet-nio/tests/pico-usb -B /tmp/nio-pico-usb-tests`,
  `cmake --build /tmp/nio-pico-usb-tests -j4`, then
  `ctest --test-dir /tmp/nio-pico-usb-tests --output-on-failure` — passed,
  five cases including 100000 bytes in each direction on two native threads.
- TLS allocator prerequisite: `cmake -S repos/fujinet-nio/tests/pico-tls -B /tmp/nio-pico-tls-tests`,
  `cmake --build /tmp/nio-pico-tls-tests -j8`, then
  `ctest --test-dir /tmp/nio-pico-tls-tests --output-on-failure` — 3/3 passed
  (implementer); actual SDK allocator, old-pool negative control and cleanup.
- Size-report fixture command below — 3/3 passed, including per-core stacks.
- `python3 repos/fujinet-nio/pico2w/size_report.py /tmp/nio-pico2w-build/fujinet_nio_pico2w.elf.map --json`
- `python3 -m unittest discover -s repos/fujinet-nio/tests -p test_pico_size_report.py`
- Run source-list generator after adding sources, inspect Pico exclusion, restore
  only incidental generated changes. `git diff --check`; owning repo status clean.

No full POSIX/ESP32 matrix unless shared production files change. Native tests and
map evidence establish ownership/bounds and linkability, not physical concurrency,
USB throughput, flash pause duration, or runtime stack/heap peaks.

## Implementation verification results

TLS prerequisite commit `20ce8f57`: actual SDK ALTCP allocator, lwIP heap and
mbedTLS configuration tests pass with two certificate/state/context setups;
old 24 KiB negative control fails setup as expected. Host setup peak is 75000
bytes in the 128 KiB pool, with zero allocations after teardown. Full handshakes
and physical peaks remain pending.

Commands run after sourcing `scripts/env.sh`:

- `cmake -S repos/fujinet-nio/tests/pico-tls -B /tmp/nio-pico-tls-tests`,
  `cmake --build /tmp/nio-pico-tls-tests -j8`,
  `ctest --test-dir /tmp/nio-pico-tls-tests --output-on-failure`: 3/3 pass.
- Pico configure and build commands listed above: ELF/UF2 linked successfully.
- Raw native configure/build/CTest commands listed above: 6/6 pass including
  production adapter lifecycle, flash-init failure, USB-init failure and timeout.
- `cmake -S repos/fujinet-nio/tests/pico-usb -B /tmp/nio-pico-usb-tests`,
  `cmake --build /tmp/nio-pico-usb-tests -j4`,
  `ctest --test-dir /tmp/nio-pico-usb-tests --output-on-failure`: 5 bridge cases
  pass, including two-thread 100000-byte bidirectional ordered stress.
- Size report and unittest commands listed above: 3 fixture tests pass;
  1156328 flash bytes, 349740 static RAM bytes, 2048 minimum heap reservation,
  16384 core-0 stack bytes and 4096 core-1 stack bytes.
- `arm-none-eabi-nm -n /tmp/nio-pico2w-build/fujinet_nio_pico2w.elf`: core-0
  stack 0x2007c000–0x20080000, core-1 stack 0x20080000–0x20081000;
  `__HeapLimit` is 0x2007c000.
- In owning repository, `python3 scripts/update_cmake_sources.py`: inspected
  generated POSIX/ESP32 source lists and restored incidental template rewrites
  (including an unwanted Pico build profile in the generated ESP32 list).
- `git diff --check`: passes.

The SDK ROM launch handshake precedes the bounded 2-second application readiness
wait. Worker readiness includes flash lockout registration and TinyUSB init.
Hardware concurrency, latency, reconnect timing, flash pauses and runtime stack/
heap peaks remain explicitly pending; no board was available.

## Review disposition

Three independent layers reviewed the baseline-to-feature diff: blind,
edge-case and verification-gap review.

- Patch: order bus-reset invalidation with TinyUSB task callbacks, preserving
  new-session data received after reconnect within a single task call.
- Patch: reject a slow core-0 response if its read session expired before write.
- Defer: shared FujiBus partial/queued framing does not observe connection epochs;
  predates this change and is recorded in deferred-work.md. Narrow README claims.
- No additional boot abstraction: production main's direct failing-startup
  return was reviewed; actual worker failure/timeout paths have executable tests.
- Separate bridge/worker tests deliberately cover concurrency and SDK call
  ownership at their respective boundaries. They do not simulate physical IRQ
  timing or SDK lockout. Hardware acceptance remains explicitly pending.
- Successful TLS context setup is not handshake headroom evidence. Docs and
  measurements retain that distinction; no live handshake or runtime-fit claim.

Final review fixes committed as `f0bbe1ec` after the dual-core implementation
`f34670a1` and separate TLS prerequisite `20ce8f57`. Native worker 6/6,
bridge six cases (including threaded stress), size fixtures 3/3 and Pico link
pass. Parent independently reran native worker/bridge checks and parsed the final
ELF/map: 1156328 flash bytes, 349740 static RAM bytes, stacks 16384 + 4096.
A targeted independent re-review of reset ordering and stale-response handling
found no remaining introduced defects. Source repository is clean. No push.

## Suggested Review Order

- Boot requires a ready USB worker before mounting flash.
  [main_pico.cpp:40](../../repos/fujinet-nio/src/app/main_pico.cpp#L40)

- Core 1 owns TinyUSB initialization, callbacks and service.
  [usb_service.cpp:1](../../repos/fujinet-nio/src/platform/pico/usb_service.cpp#L1)

- Bounded queues serialize ownership, backpressure and session transitions.
  [usb_bridge.h:1](../../repos/fujinet-nio/src/platform/pico/detail/usb_bridge.h#L1)

- Core 0 accesses the bridge through the Channel interface.
  [channel_factory.cpp:1](../../repos/fujinet-nio/src/platform/pico/channel_factory.cpp#L1)

- SDK multicore lockout and distinct stack reservations support the split.
  [CMakeLists.txt:1](../../repos/fujinet-nio/pico2w/CMakeLists.txt#L1)

- The separately corrected pool accommodates actual SDK TLS context allocations.
  [lwipopts.h:1](../../repos/fujinet-nio/pico2w/lwipopts.h#L1)

- Production-adapter tests check core ownership, startup failures and session handling.
  [test_usb_worker.cpp:1](../../repos/fujinet-nio/tests/pico/test_usb_worker.cpp#L1)

- Threaded bridge tests exercise byte ordering, capacity and lifecycle boundaries.
  [test_bridge.cpp:1](../../repos/fujinet-nio/tests/pico-usb/test_bridge.cpp#L1)

- Build evidence and outstanding physical acceptance remain explicitly distinguished.
  [README.md:1](../../repos/fujinet-nio/pico2w/README.md#L1)

