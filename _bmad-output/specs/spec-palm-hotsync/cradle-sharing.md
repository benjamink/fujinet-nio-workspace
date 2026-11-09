# Cradle sharing: one serial line, two protocols

## Proposed shape

```text
            UART / POSIX serial / pty  (single owner)
                         |
               PalmCradleChannel  (io::Channel adapter, owns the line)
                 |                         |
   Channel view for FujiBusTransport   HotSync lease (link: read / write / set_baud)
   (unchanged SlipFramer + transport)  used only by the HotSync service
```

- The adapter wraps the platform channel the same way the Atari SIO and NetSIO adapters wrap theirs. `FujiBusTransport` and the devices are unchanged.
- Baud control is injected as a small interface implemented by the platform glue (ESP32 `UartChannel::setBaudrate`, POSIX termios). It is not added to `io::Channel`.
- Selected by build profile or config. Builds without a cradle construct no adapter (no `#ifdef`).

## Behaviour carried over from classic (proven on hardware)

1. Every valid FujiBus frame updates "host active". While a frame has arrived within the last 60 s, the line is never lent.
2. Bytes outside any SLIP frame with no valid frames alongside them end that hold early. This is what 9600-baud SLP looks like when read at 115200.
3. When idle, every 1.5 s the adapter:
   - switches to 9600;
   - waits 50 ms;
   - lets the HotSync service listen up to 1.5 s for a CMP WAKEUP.
   The deadline covers only the WAKEUP wait, not the Palm's ACK of INIT.
4. On WAKEUP, the lease lasts the whole session, including the CMP baud change (plus the 50 ms settle). On release the adapter restores 115200 and discards bytes received at the old rate.
5. While leased, FujiBus requests get no reply; the Palm client's retry policy covers this (`palm-protocols.md`).
6. Discard only bytes already pending. Do not wait for the line to go quiet: a chattering cradle never does.

## What differs from classic

- No bus hooks: classic added `_rs232_lend_line()` to `systemBus::service()` and a passive virtual device. Here the adapter is the only owner.
- The hand-off state machine is a pure class with injected clock and baud control, so it gets unit tests (classic had none).
- Stray bytes are not forwarded to any modem device.
- Emulators: CloudpilotEmu connects through a socat pty to the POSIX serial path, so no separate 6416 listener is needed.

## Open design points for review

- **Explicit "sync now".** The FN HotSync app sends a FujiBus command that opens a window at once and skips the periodic probing.
- **Probing while a Palm app is active.** Accept the 60-second rule, or have the client announce itself?
