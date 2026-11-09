# Failure modes learned on classic hardware

Each one becomes a test or an explicit requirement in the NIO implementation.

## Link and handshake

| Failure | Required behaviour |
|---|---|
| A WAKEUP late in a listening window lost the Palm's ACK because the window deadline also bounded the INIT exchange | Bound only the WAKEUP wait. The handshake that follows has its own PADP timeouts. |
| A retransmitted WAKEUP was taken as the ACK of INIT | The PADP layer distinguishes a duplicate WAKEUP from an ACK |
| A request sent right after a baud change was lost | 50 ms settle after every baud change, both directions |
| `discardInput()` waited for silence that never came | Drop only bytes already pending |
| A 10 s app-activity hold let probing interrupt apps that poll every few tens of seconds | 60 s hold, ended early by stray non-SLIP bytes |
| A cradle behind a null modem never raises RTS | Cradle line runs with hardware flow control off |

## Date Book conduit (CAP-6)

| Failure | Required behaviour |
|---|---|
| Events overlapping the window edges duplicated on every sync | Map entries outside the fetched window are kept, not re-created |
| Window wider than a capped fetch (300 events), so unfetched events read as cancelled and were deleted | Narrow the window to what the fetch covered |
| A map write interrupted, or an unreadable map, wiped or duplicated records | Write to a temp file and rename. On an unreadable map, leave the Date Book untouched. |
| Maps shared between users or devices | Map per user and device ID |
| A record deleted on the Palm was resurrected | Treat it as gone; do not re-create it |
| A record edited on the Palm was overwritten or deleted | Never modify or delete a record the Palm has changed |
| A Palm that never opened Date Book has no `DatebookDB` | Log it in the sync log and continue |
| Uids with unsafe characters | Percent-encode them in the map |
| Calendar cache read from two contexts | Guard shared calendar state |

## Resources

| Failure | Required behaviour |
|---|---|
| A whole database landed in internal DRAM on ESP32 | Cap the size; use PSRAM |
| Settings applied only after a restart | Decide in review whether HotSync settings are live or restart-only, and say so in the diagnostics output |
