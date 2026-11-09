# Palm protocols: what NIO must speak

## HotSync stack (FujiNet is the desktop side)

| Layer | Facts that bind the implementation |
|---|---|
| SLP | Signature `BE EF ED`; dest/src socket (3 = DLP); type (0 system, 2 PADP, 3 loopback); BE16 length; xid; 8-bit sum header checksum; trailing CRC-16/CCITT (poly 0x1021, init 0) over header and body. The reader must resync on garbage. |
| PADP | Data/ACK; 512-byte fragments; 2 s ACK wait; 10 retries; long-form flag; duplicate detection. A retransmitted WAKEUP must not be taken as an ACK. |
| CMP | Palm sends WAKEUP(1) at 9600. Reply INIT(2) on xid `0xFF` with flags `LONG_FORM_PADP\|CHANGE_BAUD` and baud = min(Palm offer, 115200). Wait 50 ms after every baud change; requests sent sooner are lost and cost a 2 s PADP retry. |
| NetSync | TCP 14238. 6-byte header (type 1, xid, u32 length), then a fixed 3-step handshake (22/50/8-byte requests, canned replies). Cap messages at 1 MB. |
| DLP | Short/long argument IDs; response bit `0x80`. Host DLP version 1.4; 30 s reply wait. Commands used: ReadSysInfo, Read/WriteUserInfo, ReadDBList, OpenConduit, Open/Create/Close/DeleteDB, ReadOpenDBInfo, read/write AppBlock and SortBlock, GetSysDateTime/SetSysDateTime, ReadRecord (by index and by ID), WriteRecord, DeleteRecord, ReadResource, WriteResource, AddSyncLogEntry, ResetSystem, EndOfSync. |
| PDB/PRC | Read and write both formats; Palm epoch (1904) dates. |

**Session order:**

1. Identify the user. A device with no user gets the configured name and a new ID.
2. OpenConduit.
3. Read the Palm's clock for its time zone.
4. Install queued files.
5. Date Book conduit (CAP-6).
6. Backup, per policy `none`, `flagged` or `all`. Skip "Unsaved Preferences".
7. Finish: stamp user info with PC ID `0x464A4E54` ("FJNT"), set the clock, EndOfSync.

**Storage layout** (relative to the HotSync root on the persistent filesystem):

- `install/`: queue; files move to `installed/` once installed
- `backup/<user>/`
- `state/<user>-<id>/` (e.g. the `datebook.map`)
- File names must be FAT-safe.

## FujiBus from Palm apps

- Framing is identical to NIO FujiBus: SLIP, 6-byte header, LE parameters, folded-carry checksum.
- Link settings: 115200 8N1, no flow control, cradle port. The Palm never changes baud for FujiBus.
- Semantics follow NIO (`repos/fujinet-nio/docs/protocol_reference.md`), not classic ACK/NAK, so the Palm client is rebuilt on `fujinet-nio-lib`.

**Classic capabilities the apps rely on, to be mapped onto NIO devices:**

| Classic (`fujinet-palm/common`) | Used for | NIO mapping to confirm |
|---|---|---|
| `0x70 0xE8` GET_ADAPTERCONFIG | FN Test, FN HotSync status | FujiDevice GetInfo `0x01` / Wifi `0xF3` |
| `0x71` N1 open/status/read/write/close (HTTP, TCP, HTTPS) | Lobby, Bounce World, Hold'em, FujiPet | NetworkDevice `0xFD` handle commands |
| `0x70` host slots, directory read, COPY_FILE to `/palm/install/` | FN HotSync install from TNFS | FileDevice `0xFE` / HostService `0xF0` copy into the HotSync install queue |

## Retry policy the Palm client must keep

The policy exists because the line can be lent to HotSync for up to 1.5 s:

- Flush receive, send, `SrmSendWait`, then wait 0.7 s for a frame. Up to 8 attempts. Ignore replies from other devices.
- Idempotent commands retry. READ and WRITE are sent once. If the link has been idle for more than 5 s, a STATUS first reclaims it.
- Network open: 2 attempts × 10 s. The first STATUS after an HTTP open waits long (the fetch happens then) and is not resent.
- Long copies: a quick info request first, so the request lands in a bus window; then 3 attempts × 60 s.
