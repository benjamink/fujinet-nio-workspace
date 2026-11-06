# Amiga Zorro USB bring up

Status: deliverable 1 implementation in progress; hardware results pending.
Direction agreed: 2026-11-06.

## Goal and working method

Prove RP2350 USB host to ESP32-S3 USB device communication and independent
flashing through one external USB connector, then connect that link to the
Amiga Zorro mailbox. Use the checklists below directly, outside BMad. Do not
generate epics, stories, context packs or a replacement spec hierarchy.

Complete one bounded deliverable at a time. Record commands, results and the
next unchecked item; add work only when a concrete failure requires it.
Keep implementation details and hardware procedures in their owning repos.
This file owns cross-repository scope, dependencies and acceptance. Move it
to `completed/` when all three deliverables are accepted.

## Starting position

- The [native packet contract](../repos/fujinet-nio/docs/native-packet-contract.md)
  and software retry containment are accepted, as recorded in the
  [faster-backends goal](amiga-faster-backends.md). Preserve that work.
- The [hardware pin-budget correction](../repos/fujinet-nio-hardware/amiga/docs/eventual-board-considerations.md)
  identifies GP2–GP7 as both the laboratory SPI signals and A2–A7 in the
  proposed bus mapping. Do not transfer that SPI wiring to the integrated
  board. Audit the actual Amiga schematic rather than assuming a development
  board or Springboard pin table is the final Zorro allocation.
- The [SPI evidence ledger](../repos/fujinet-nio/bridges/rp2350-zorro/docs/link-feasibility-evidence.md)
  remains useful for ownership, fault handling and measured fixture behaviour.
  Its rates and recovery results do not qualify the USB replacement.
- Mark has performed real-Amiga timing captures with the 32-channel analyzer.
  Index the existing evidence and conclusions; repeat only measurements needed
  for an unresolved decision or affected by implementation changes.
- The [Springboard bridge](../repos/fujinet-nio/bridges/rp2350-springboard/README.md)
  proves useful bus and packet-link work. Its documented working USB path is
  RP2350 device to NIO on a computer; ESP32 hosting is future work there.
- The [bridge ABI](../repos/fujinet-nio/bridges/rp2350-zorro/docs/bridge-packet-abi.md)
  is still a draft and contains obsolete SPI-specific assumptions. Its
  whole-packet ownership and unknown-completion rules remain the basis.

## Selected POC design

```text
Amiga mailbox <-> RP2350 <-> USB CDC / PacketLink <-> ESP32-S3 NIO
                  host                              device
```

Reuse [PacketLink](../repos/fujinet-nio/docs/packet_link.md), including framing,
CRC, capacity negotiation, generations and explicit completions. CDC supplies
a byte stream, not FujiBus packet boundaries. Reuse the Springboard portable
controller where suitable; adapt its USB I/O to host mode. Keep one outstanding
exchange and no automatic replay after unknown completion.

Start with the existing 4096-byte raw-packet capacity. Check real request and
response sizes before fixing the production capacity; the old 240-byte SPI
fixture limit is not a production requirement. The ESP already has the
`fujibus-link-usbcdc-freenove-s3-wroom-1-n16r8`
[build profile](../repos/fujinet-nio/docs/build_profiles.md); confirm the actual
board and flash/PSRAM configuration before using it. Keep protocol data and
logs on their separate CDC interfaces.

Use manual mode selection initially, with USB-rated switching and a defined
disconnect state. Flashing is sequential and suspends normal communication.

| Mode | USB data connection | Entry and recovery |
| --- | --- | --- |
| Run | RP host to ESP device; external PC data isolated | Normal firmware |
| Flash RP | PC to RP; internal ESP data path isolated | Physical BOOTSEL and reset |
| Flash ESP | PC to ESP; internal RP data path isolated | Physical BOOT and reset |

The circuit must define VBUS supply, sensing and backfeed prevention in every
mode, USB-C connection requirements, and switching without connecting two
hosts. Keep RP SWD/RUN and ESP boot/reset service access. Recovery must not
depend on either application firmware or consume unbudgeted bus GPIOs.

RP supports [USB host/device operation and ROM programming](https://www.raspberrypi.com/documentation/microcontrollers/microcontroller-chips.html).
ESP supports [direct USB flashing](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/establish-serial-connection.html),
but its OTG and Serial/JTAG controllers
[share the internal PHY](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html).
Treat runtime and bootloader enumeration as distinct modes. A plain hub alone
does not solve this host-routing problem.

## Deliverable 1 Shared USB flashing and link POC

Keep the Amiga disconnected. Firmware owner: `repos/fujinet-nio`, with the
isolated RP experiment under `bridges/rp2350-zorro/`. Circuit and fixture
owner: `repos/fujinet-nio-hardware/amiga/`. Put reproducible build, wiring and
run instructions beside those implementations.

Implementation entry point: [USB host bench probe](../repos/fujinet-nio/bridges/rp2350-zorro/lab/usb-host/README.md).
Confirmed bench inventory: Waveshare Core2350B with RP Tiny Adapter B
(USB-C, BOOT and RESET), and an ESP32-S3-WROOM-1 N16R8 on a 44-pin carrier
with two USB-C sockets and BOOT/RST. Exact carrier USB/power routing still
needs confirmation. The boards share ground; physical acceptance is open.

- [ ] Identify the two boards and USB connectors; document the three-mode
  data/power circuit and controls. Check isolation and power paths before
  connecting the fixture to the PC.
- [x] Build the smallest RP USB-host harness and the matching ESP PacketLink
  profile, reusing existing protocol code. Record exact build/flash commands.
  Software checks: [initial verification](../repos/fujinet-nio/bridges/rp2350-zorro/lab/usb-host/VERIFICATION.md).
- [ ] Flash each processor through the same external connector using physical
  boot controls, including with nonfunctional application firmware. Verify
  that neither processor needs its peer's application to recover.
- [ ] Return to Run mode, enumerate the correct CDC interface, synchronize and
  complete a real `Clock.GetTime`. Verify known binary data across multiple
  USB transfers up to capacity, plus explicit capacity-plus-one rejection.
- [ ] Reset either endpoint and disconnect the link during pending exchanges.
  Observe bounded failure, unknown completion where appropriate, fresh
  synchronization and a successful new request, without stale completion or
  replay of the uncertain request. Include a stalled receiver/partial record.
- [ ] Record repeatable latency and useful payload throughput, firmware
  revisions, fixture identity and recovery results. Check both cold startup
  and repeated Run/Flash/Run cycles.

Exit: both chips can be recovered through the shared connector independently,
and the same fixture carries real NIO requests with bounded fault recovery.
Record measured performance; do not infer it from USB signalling speed.
Stop this deliverable here: no custom PCB, automatic updater, vendor USB class,
Zorro driver, service redesign or accelerator work.

## Deliverable 2 Resolve the integrated design

Begin after the POC establishes the chosen topology. Hardware details belong
in the hardware repo; link semantics belong in the bridge ABI and PacketLink
docs. Preserve the existing BMad artifacts as history and reference material.

- [ ] Complete the actual board's signal-by-signal budget, including Zorro,
  USB switch controls, VBUS sensing/control, debug, boot and reset. Record the
  chosen routing/power design and independent recovery access before layout.
- [ ] Update the draft ABI to use the USB PacketLink profile, replacing SPI
  clocks and READY/DATA_AVAILABLE assumptions. Record capacity, generation,
  completion, disconnect and version rules; check existing caller sizes.
- [ ] Index existing Amiga captures and resolve only remaining mailbox/address,
  byte/word access, output-enable and timing decisions. Record a concise design
  decision covering the mailbox and safe electrical behaviour before active
  bus implementation.

Exit: a coherent pin budget, link contract and mailbox design support the first
active exchange. Carry forward the substantive software and electrical
requirements from the old plan; satisfy them with focused evidence rather
than rerunning its story workflow. This POC does not approve production layout.

## Deliverable 3 First real Amiga exchange

Owners: bridge and ESP code in `repos/fujinet-nio`; the Amiga backend in
`repos/fujinet-nio-driver`; cross-repository guest tests in
`integration-tests/amiberry` only where useful. Change `fujinet-nio-lib` only
if its existing public contract actually needs an extension.

- [ ] Implement the smallest mailbox/backend path to the ESP clock service.
  Keep Zorro bus cycles serviced locally; wait for USB completion through
  mailbox state, never by holding a bus cycle open for an ESP response.
- [ ] Demonstrate a disk-sector read and write/read-back on disposable media
  through the existing services. Verify reset/disconnect containment without
  changing application APIs or introducing physical transport failover.
- [ ] Check active bus timing and data-line release under concurrent USB
  traffic. Record end-to-end latency, throughput and any remaining limits.

Exit: a real Amiga request reaches NIO over Zorro and USB, returns the correct
result, and recovers safely from the tested faults. Broader production parity
and release acceptance remain in the faster-backends goal; they are not extra
prerequisites for demonstrating this first slice.

## Verification and handoff

Follow [the test policy](../docs/agent-test-policy.md), sourcing
`scripts/env.sh` first. Select and run the cheapest relevant check in each
changed repository. Record exact commands and outcomes beside the owning
implementation; complete `make check` for any library changes. Builds and
host tests do not replace the named physical checks above.

Keep one short result record per deliverable: commits/images, board and wiring
revision, commands, observed results, evidence locations and the next unchecked
item. If hardware is unavailable, leave its boxes open and state the specific
missing run. Do not expand the plan to compensate.
