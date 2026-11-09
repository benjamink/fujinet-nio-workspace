# Amiga Zorro USB bring up

Status: deliverable 1 feasibility accepted for design; deliverable 2 tooling selected and locally verified.
Direction agreed: 2026-11-06.

2026-11-09 scope decision: the demonstrated USB link, capacity exchange,
reset/recovery and manual shared-connector flashing are sufficient to proceed.
Do not require corrupted application images, more reset repetitions or a
standalone throughput campaign before circuit design. Physical BOOT at power-on
already exercised application-independent ROM entry with the peer isolated.
This accepts feasibility, not a finished switch circuit or production layout.

Next: use the hardware repository's
[tooling guide](../repos/fujinet-nio-hardware/tools/kicad/README.md) and
[agent instructions](../repos/fujinet-nio-hardware/AGENTS.md), then resolve the
USB/power circuit and Zorro pin budget. No new BMad workflow.

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

The authoritative hardware mode, power and user-serviceable recovery contract
is [USB connector strategy](../repos/fujinet-nio-hardware/amiga/docs/eventual-board-considerations.md#usb-connector-strategy).
The [bench guide](../repos/fujinet-nio/bridges/rp2350-zorro/lab/usb-host/README.md)
documents the manually rewired fixture and its practical precautions.

## Deliverable 1 Shared USB flashing and link POC

Keep the Amiga disconnected. Firmware owner: `repos/fujinet-nio`, with the
isolated RP experiment under `bridges/rp2350-zorro/`. Circuit and fixture
owner: `repos/fujinet-nio-hardware/amiga/`. Put reproducible build, wiring and
run instructions beside those implementations.

Implementation entry point: [USB host bench probe](../repos/fujinet-nio/bridges/rp2350-zorro/lab/usb-host/README.md).
Confirmed bench inventory: Waveshare Core2350B with RP Tiny Adapter B
(USB-C, BOOT and RESET), and an ESP32-S3-WROOM-1 N16R8 on a 44-pin carrier
with two USB-C sockets and BOOT/RST. Exact carrier USB/power routing still
needs confirmation only if that carrier routing is relied upon in a new fixture.
The final integrated circuit must establish its own explicit power paths.

- [x] Identify the boards and demonstrate the manually rewired three-mode
  fixture with isolated power/data paths. Integrated switching belongs to
  deliverable 2; it was not tested by manually moving the wires.
- [x] Build the smallest RP USB-host harness and the matching ESP PacketLink
  profile, reusing existing protocol code. Record exact build/flash commands.
  Software checks: [initial verification](../repos/fujinet-nio/bridges/rp2350-zorro/lab/usb-host/VERIFICATION.md).
- [x] Flash each processor through the same external connector using physical
  ROM boot controls at power-on, with its peer isolated. Return to Run and
  complete status/clock. Deliberately corrupted application images were not
  tested and are not a design-entry prerequisite.
- [x] Return to Run mode, enumerate the correct CDC interface, synchronize and
  complete a real `Clock.GetTime`. Verify known binary data across multiple
  USB transfers up to capacity, plus explicit local capacity-plus-one rejection.
- [x] Demonstrate ESP reset with pending=0 and pending=1, retained fault for
  unknown completion, explicit resync and a new successful request. Demonstrate
  RP reset during streaming and return to communication. RP pending-at-reset
  was not observable; do not claim it was proven.
- [x] Record fixture and functional results in the bench verification ledger.
  Recorded exchange timings are observations, not a sustained-throughput claim.

Carry forward only when relevant: stalled receiver/partial-record handling to
bridge integration verification; cold-start service readiness to firmware
integration; throughput to the real Amiga slice. Verify actual mode selection,
isolation and Run/Flash/Run transitions when the selected switch circuit exists.

Accepted exit for design: both chips entered ROM and were flashed independently
through the same connector, and the restored fixture carries real NIO requests
with the fault recovery recorded above. Do not infer performance from USB speed.
Stop this deliverable here: no custom PCB, automatic updater, vendor USB class,
Zorro driver, service redesign or accelerator work.

## Deliverable 2 Resolve the integrated design

Proceed now using the accepted POC evidence. Hardware details belong
in the hardware repo; link semantics belong in the bridge ABI and PacketLink
docs. Preserve the existing BMad artifacts as history and reference material.

2026-11-09 candidate progress: live configured KiCad MCP calls succeeded and
the passive breakout was inspected without saving it. The separate
[integrated R0 proposal](../repos/fujinet-nio-hardware/amiga/integrated-r0/proposal.md)
contains a revised complete RP allocation and an implemented USB/power/recovery
subcircuit (170 independently checked pin assignments, four USB selector states,
zero KiCad ERC findings). Processor/Zorro sheets, final power sign-off and PCB
are unfinished; the checkboxes below remain open. The user has since clarified that the real Amiga captures were not committed.
The supplied screenshots and two-analyzer/32-channel observation are accepted
bring-up evidence; no CSV conversion tool is needed before design. They do not
qualify timing of the new active buffers. Do not repeat USB feasibility tests.

2026-11-09 next-stage decision: primary hardware plugs directly into the A500
86-contact edge through a female socket; the manufactured passive breakout and
purchased adapter remain bench infrastructure. A2000 is a separate future
100-contact card variant. The new
[A500 R1 candidate](../repos/fujinet-nio-hardware/amiga/integrated-a500-r1/README.md)
contains seven functional circuit sheets plus overview, both processors,
SD storage and implemented bus interlocks. Native verification checks 803 pad
assignments/183 complete nets, 81 RP pads, 32,768 static interlock cases and
USB selections. Thirty external-host ERC model findings remain visible.
Power protection/current behaviour, A500 timing, socket mechanics, final BOM
and PCB layout remain open; this is a circuit-review milestone, not electrical
or fabrication approval. Hardware candidate committed locally as `6278f8cb`; no workspace submodule pin
is advanced.

2026-11-09 electrical-review continuation: the
[A500 R2 candidate](../repos/fujinet-nio-hardware/amiga/integrated-a500-r2/README.md)
corrects R1's local-DTACK handshake. Commodore documents motherboard-generated
DTACK and an XRDY holdoff deadline of 60ns; R2 implements that holdoff, per-cycle
completion/read-drive latches and BERR output inhibition without extra RP GPIO.
Native checks cover 831 pin assignments on 189 nets, 65,536 static cases and
65,536 latch sequences. Thirty-two external-host ERC findings remain visible.
The provisional timing allocation is documented, not physical qualification.
Power protection/CC behaviour, socket mechanics, BOM and layout remain open;
PIO sequencing and watchdog recovery must precede active attachment. Existing
USB demonstrations and passive captures remain accepted; no repeat experiment
is requested. R1 and the released passive hardware are preserved.
Hardware milestone: local commit `658eb316`; workspace submodule pin unchanged.

2026-11-09 input-power continuation: the
[A500 R3 candidate](../repos/fujinet-nio-hardware/amiga/integrated-a500-r3/README.md)
adds TPS259630 current/voltage protection, LM66100 reverse blocking and CC ESD,
without changing the RP GPIO allocation or R2 bus handshake. Native checks
cover 188 physical components, 864 pin assignments and 195 complete nets;
33 explicitly reviewed ERC findings remain. The conditional 1.166A input
budget fits the calculated 1.197A minimum limit with a small margin.
Manufacturer socket dimensions and component candidates are recorded, but
contact orientation/case fit, final BOM, fault transients and PCB layout remain
open. R0–R2 and released hardware are preserved. Hardware milestone: local
commit `0e686501`; no workspace pin is advanced.

2026-11-09 physical-design continuation: the separate
[A500 R4 candidate](../repos/fujinet-nio-hardware/amiga/integrated-a500-r4/README.md)
contains the first horizontal 105 × 124 mm PCB placement, all 188 physical
components, a reference-derived 86-contact socket footprint and four mounting
holes. Native checks verify all 864 functional pin assignments and zero
schematic/PCB parity findings. The saved board remains unrouted (499
unconnected items); critical power/USB layout, stackup, final BOM and
mechanical qualification remain open. The RP pin budget and independent
recovery allocation are complete as a design decision. No fabrication release,
new bench experiment or workspace submodule-pin change is implied. Hardware
placement milestone is committed locally as `30123379`.

- [x] Complete the actual board's signal-by-signal budget, including Zorro,
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
