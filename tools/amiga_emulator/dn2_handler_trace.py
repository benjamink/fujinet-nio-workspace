"""Trace DOS handler identity and packet delivery across dynamic mounts."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import ipc
from .debug_snapshot import (
    live_filesystem_processes,
    parse_registers,
    read_memory,
    resolve_dos_device_task,
)


PUTMSG_LVO = 0x16E


def resolve_exec_vector(socket_path: Path, exec_base: int, lvo: int) -> int:
    """Resolve an Exec library vector trampoline to its implementation PC."""
    vector = exec_base - lvo
    opcode = read_memory(socket_path, vector, 2)
    if opcode == 0x4EF9:  # JMP absolute long
        return read_memory(socket_path, vector + 2, 4)
    if opcode == 0x4EB9:  # JSR absolute long
        return read_memory(socket_path, vector + 2, 4)
    return vector


def write_snapshot(log, socket_path: Path, label: str,
                   device_names: list[str],
                   processes: list[dict[str, int | str]]) -> None:
    tasks: dict[str, int] = {}
    for device_name in device_names:
        try:
            tasks[device_name] = resolve_dos_device_task(socket_path, device_name)
        except LookupError:
            tasks[device_name] = 0
    task_text = " ".join(
        f"dos_{device_name.lower()}_task={task:#x}"
        for device_name, task in tasks.items()
    )
    log.write(f"SNAPSHOT label={label} count={len(processes)} {task_text}\n")
    for process in processes:
        device_name = str(process["name"]).upper()
        log.write(
            f"{device_name} process={int(process['address']):#x} port={int(process['port']):#x} "
            f"state={process['state']} sigwait={int(process['sig_wait']):#x} "
            f"filesystem_task={int(process['filesystem_task']):#x}\n"
        )
    log.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--device", action="append", default=[],
                        help="DOS device to trace (repeatable; default: DN2)")
    parser.add_argument("--poll-seconds", type=float, default=1.0,
                        help="minimum interval between live task scans")
    parser.add_argument("--total-timeout", type=float, default=75.0)
    args = parser.parse_args(argv)
    socket_path = Path(args.socket)
    output = Path(args.output_dir)
    log_path = output / "dn2-handler-trace.log"
    device_names = [name.rstrip(":").upper() for name in args.device] or ["DN2"]
    device_set = set(device_names)
    deadline = time.monotonic() + args.total_timeout
    previous: set[int] = set()
    known_ports: dict[int, tuple[int, str]] = {}
    try:
        # The runner paused before bridge startup. Arm Exec PutMsg before the
        # unchanged guest sequence can create or use either DN2 handler.
        exec_base = read_memory(socket_path, 4, 4)
        putmsg_vector = exec_base - PUTMSG_LVO
        putmsg = resolve_exec_vector(socket_path, exec_base, PUTMSG_LVO)
        ipc.request(socket_path, "SET_BREAKPOINT", hex(putmsg))
        with log_path.open("w", encoding="ascii") as log:
            log.write(f"PUTMSG_VECTOR {putmsg_vector:#x} PUTMSG_TARGET {putmsg:#x}\n")
            ipc.request(socket_path, "DEBUG_CONTINUE")
            while time.monotonic() < deadline:
                try:
                    processes = live_filesystem_processes(socket_path, device_set)
                except (OSError, RuntimeError) as error:
                    log.write(f"IPC_ERROR stage=task-scan error={error!r}\n")
                    log.flush()
                    time.sleep(args.poll_seconds)
                    continue
                current = {int(process["address"]) for process in processes}
                if current != previous:
                    label = "initial" if not previous else "handler-set-changed"
                    try:
                        write_snapshot(log, socket_path, label, device_names, processes)
                    except (OSError, RuntimeError) as error:
                        log.write(f"IPC_ERROR stage=snapshot error={error!r}\n")
                        log.flush()
                    previous = current
                known_ports = {
                    int(process["port"]): (int(process["address"]), str(process["name"]).upper())
                    for process in processes
                }

                try:
                    registers = parse_registers(ipc.request(socket_path, "GET_CPU_REGS"))
                except (OSError, RuntimeError) as error:
                    log.write(f"IPC_ERROR stage=registers error={error!r}\n")
                    log.flush()
                    time.sleep(args.poll_seconds)
                    continue
                if registers.get("PC") == putmsg:
                    port = registers["A0"]
                    message = registers["A1"]
                    if port in known_ports:
                        process, device_name = known_ports[port]
                        packet = message + 20
                        try:
                            packet_type = read_memory(socket_path, packet + 8, 4)
                            packet_arg1 = read_memory(socket_path, packet + 12, 4)
                            reply_port = read_memory(socket_path, message + 14, 4)
                        except (OSError, RuntimeError) as error:
                            log.write(f"IPC_ERROR stage=packet error={error!r}\n")
                            log.flush()
                            ipc.request(socket_path, "DEBUG_CONTINUE")
                            continue
                        log.write(
                            f"PUTMSG device={device_name} process={process:#x} port={port:#x} "
                            f"message={message:#x} reply_port={reply_port:#x} "
                            f"packet={packet:#x} packet_type={packet_type:#x} "
                            f"packet_arg1={packet_arg1:#x}\n"
                        )
                        log.flush()
                    ipc.request(socket_path, "DEBUG_CONTINUE")
                else:
                    time.sleep(args.poll_seconds)
    finally:
        try:
            ipc.request(socket_path, "QUIT")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
