# BBC library and ROM modernisation

User-approved sequence, 2026-11-04. Preserve ROM-backed BBC architecture and
measure linked CODE/BSS and soft65c02 cycles; use Beebium for MOS integration.

- [x] Main-header capability inventory and independent BBC/BBC-clib link gate.
  Library commit 31629fe4; initially 93 declarations, now 94 including fn_bbc.h.
- [x] ListPages/filter through existing OSWORD device call, without ROM growth.
  Library commit c149ecf2; shared wire vectors and dedicated Beebium test pass.
- [x] Wi-Fi archive granularity. Library commit be299285; status-only CODE
  5421 -> 2514, join-only 5421 -> 1969, BSS stays 19 bytes. BBC wire vectors
  added and a null reply-length pointer bug in set-config corrected.
- [x] Bulk network read contract and measured cycle benefit, with fallback for
  existing ROMs and tests for partial/NotReady/EOF/buffer boundaries.
- [x] Ready/read-available, preserving MOS handle ownership and ROM-buffered data.
- [x] HTTP headers, bounded caller-owned memory and safe old-ROM behavior.

All six stages are complete. Each library stage ran full make check.
DiskDevice API, shutdown and write-diagnostics gaps found by the inventory are
recorded in the owning library docs, not silently added to this work.

Owning documentation: repos/fujinet-nio-lib/docs/bbc-capabilities.md.
Baseline emulator: ~/dev/bbc/beebium upstream master 063e586b, with matching
beebium_ext_rpc_serial_plugin. Library/ROM/config launch fixtures are updated.
Evidence before/after map files: scratch/bbc-improvements/.

## Acceptance evidence

- Complete library `make check`: all configured targets, wire vectors, public
  link gates; 94 API classifications verified independently for BBC/BBC-clib.
- ROM `./run_unit_tests.sh`: passed, including bulk-read, channel-info and
  header-descriptor vectors (123 assertions in the combined focused harness).
- Library `integration-tests/beebium/./run_pytest.sh -q -rs`: 11 passed,
  2 pre-existing scaffold skips. Covers ListPages, Ready, HTTP headers,
  ordinary TCP/HTTP and cleanup after header opens.
- Five TCP/HTTP Beebium tests also passed against the old ROM, exercising
  OSBGET fallback. Unsupported new calls are covered by host/mock vectors.
- `make sizes`: BBC 15926 used / 458 free; Master 15979 / 405. Total resident
  growth 500 bytes; no additional persistent ROM workspace.
- soft65c02 prebuffered 120-byte read: 76215 -> 3644 cycles. This excludes
  network time. See owning docs for all lengths and conservative baseline.

Bulk-read commits: ROM bf8ff09f, library e8077f2b.
Readiness commits: ROM 0bf32623, library a02159fa.
Header support commits: ROM 47bb97e5, library f0e7bf5e. No firmware protocol changes or non-BBC runtime changes.
All commits remain local; workspace submodule pins deliberately unchanged.
