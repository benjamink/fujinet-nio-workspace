"""Capture the DOS ``ACTION_DIE`` request and reply for selected handlers.

Unlike the earlier handler trace this deliberately does not walk Exec's task
lists.  A normal FUMOUNT run makes enough short-lived processes that a full
walk turns debugger IPC itself into the experiment.  The DOS DeviceList gives
us the only identities required here: each selected DosNode's current task
port.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import ipc
from .debug_snapshot import (
    DOSPACKET_RES1,
    DOSPACKET_RES2,
    DOSPACKET_TYPE,
    MESSAGE_SIZE,
    parse_registers,
    read_memory,
    resolve_dos_device_task,
)
from .dn2_handler_trace import resolve_exec_vector


PUTMSG_LVO = 0x16E
REPLYMSG_LVO = 0x17A
ACTION_DIE = 5


def refresh_ports(socket_path: Path, devices: list[str]) -> dict[int, str]:
    """Return current handler ports without inspecting unrelated processes."""
    ports: dict[int, str] = {}
    for device in devices:
        try:
            port = resolve_dos_device_task(socket_path, device)
        except LookupError:
            continue
        if port:
            ports[port] = device
    return ports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--device", action="append", default=["DN0", "DN2"])
    parser.add_argument("--total-timeout", type=float, default=90.0)
    parser.add_argument("--refresh-seconds", type=float, default=0.5)
    args = parser.parse_args(argv)

    socket_path = Path(args.socket)
    output = Path(args.output_dir)
    devices = [device.rstrip(":").upper() for device in args.device]
    deadline = time.monotonic() + args.total_timeout
    next_refresh = 0.0
    ports: dict[int, str] = {}
    pending_die: dict[int, str] = {}
    armed = False
    log_path = output / "fumount-die-trace.log"

    try:
        exec_base = read_memory(socket_path, 4, 4)
        putmsg = resolve_exec_vector(socket_path, exec_base, PUTMSG_LVO)
        replymsg = resolve_exec_vector(socket_path, exec_base, REPLYMSG_LVO)
        with log_path.open("w", encoding="ascii") as log:
            log.write(f"PUTMSG {putmsg:#x} REPLYMSG {replymsg:#x} DEVICES {devices}\n")
            # Do not globally trap PutMsg during Workbench/startup.  First
            # allow the scenario to create a selected handler, then arm both
            # slots while it is paused.  A global PutMsg breakpoint otherwise
            # stops every DOS exchange before there is a target port to match.
            ipc.request(socket_path, "DEBUG_CONTINUE")
            while time.monotonic() < deadline:
                pc = None
                registers: dict[str, int] = {}
                if armed:
                    registers = parse_registers(ipc.request(socket_path, "GET_CPU_REGS"))
                    pc = registers.get("PC")
                if armed and pc == putmsg:
                    port = registers["A0"]
                    message = registers["A1"]
                    device = ports.get(port)
                    if device is not None:
                        packet = message + MESSAGE_SIZE
                        packet_type = read_memory(socket_path, packet + DOSPACKET_TYPE, 4)
                        log.write(
                            f"PUTMSG device={device} port={port:#x} message={message:#x} "
                            f"packet={packet:#x} type={packet_type:#x}\n"
                        )
                        if packet_type == ACTION_DIE:
                            pending_die[message] = device
                            log.write(
                                f"ACTION_DIE_SENT device={device} message={message:#x} "
                                f"packet={packet:#x}\n"
                            )
                        log.flush()
                    ipc.request(socket_path, "DEBUG_CONTINUE")
                    continue
                if armed and pc == replymsg:
                    message = registers["A1"]
                    device = pending_die.pop(message, None)
                    if device is not None:
                        packet = message + MESSAGE_SIZE
                        result = read_memory(socket_path, packet + DOSPACKET_RES1, 4)
                        error = read_memory(socket_path, packet + DOSPACKET_RES2, 4)
                        log.write(
                            f"ACTION_DIE_REPLY device={device} message={message:#x} "
                            f"result={result:#x} error={error}\n"
                        )
                        log.flush()
                    ipc.request(socket_path, "DEBUG_CONTINUE")
                    continue
                if time.monotonic() >= next_refresh:
                    try:
                        refreshed = refresh_ports(socket_path, devices)
                    except (OSError, RuntimeError) as error:
                        log.write(f"PORT_REFRESH_ERROR {error!r}\n")
                    else:
                        if refreshed != ports:
                            ports = refreshed
                            ports_text = " ".join(
                                f"{device}={port:#x}" for port, device in ports.items()
                            )
                            log.write(f"PORTS {ports_text}\n")
                            log.flush()
                        if ports and not armed:
                            ipc.request(socket_path, "DEBUG_ACTIVATE")
                            # Slots keep both vector breakpoints armed
                            # simultaneously once a relevant port exists.
                            ipc.request(socket_path, "SET_BREAKPOINT", hex(putmsg), "0")
                            ipc.request(socket_path, "SET_BREAKPOINT", hex(replymsg), "1")
                            armed = True
                            log.write("BREAKPOINTS_ARMED\n")
                            log.flush()
                            ipc.request(socket_path, "DEBUG_CONTINUE")
                    next_refresh = time.monotonic() + args.refresh_seconds
                time.sleep(0.15)
    finally:
        try:
            ipc.request(socket_path, "QUIT")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
