import re


def _status(result):
    match = re.search(
        r"STATUS drive=(\d+) change=(\d+) absent=(\d+) protected=(\d+)",
        result,
    )
    assert match, result
    return tuple(int(value) for value in match.groups())


def test_fumount_handler_teardown_and_busy(run_amiga_case, amiga_environment):
    results = run_amiga_case("diskdevice-fumount-handler")

    assert "LOAD RC=0" in results["fumount-load.result"]

    assert "FMOUNT IDLE RC=0" in results["fumount-idle-mount.result"]
    assert "Ejected DN1:" in results["fumount-idle-eject.result"]
    assert "FUMOUNT IDLE RC=0" in results["fumount-idle-eject.result"]
    idle_status = _status(results["fumount-idle-status.result"])
    assert idle_status[0] == 1
    assert idle_status[2] == 1

    assert "FMOUNT LIVE RC=0" in results["fumount-live-mount.result"]
    assert "DIR LIVE RC=0" in results["fumount-live-dir.result"]
    assert "KNOWN.TXT" in results["fumount-live-dir.result"].upper()
    assert "Ejected DN0:" in results["fumount-live-eject.result"]
    assert "FUMOUNT LIVE RC=0" in results["fumount-live-eject.result"]
    live_status = _status(results["fumount-live-status.result"])
    assert live_status[0] == 0
    assert live_status[2] == 1
    dos_list = results["fumount-live-dos.result"]
    # Require a real listing before asserting on DN0.
    assert "DEVICE name=DH0 type=0" in dos_list
    assert "DEVICE name=DN1 " not in dos_list
    if amiga_environment["AMIGA_ENV_ID"] == "wb31":
        # WB3.1's FFS 40.1 has no ACTION_DIE, so its handler can never exit.
        # FUMOUNT parks it (inhibited, node kept, media ejected) for the next
        # FMOUNT to reuse, rather than orphaning a task per eject.
        assert "handler parked for reuse" in results["fumount-live-eject.result"]
        assert "FIND name=DN0 flags=00000004 found=1" in dos_list
        expected_opencnt = 1
    else:
        # Successful FUMOUNT removes the DOS nodes so the resident can unload.
        assert "FIND name=DN0 flags=00000004 found=0" in dos_list
        assert "DEVICE name=DN0 " not in dos_list
        expected_opencnt = 0
    assert (
        f"DEVICE name=fujinet-disk.device found=1 opencnt={expected_opencnt}"
        in results["fumount-live-opencnt.result"]
    )
    assert "OPENCNT RC=0" in results["fumount-live-opencnt.result"]

    assert "Usage: FUMOUNT 0|...|7" in results["fumount-bad-argv.result"]
    assert "BAD ARGV RC=10" in results["fumount-bad-argv.result"]
    assert "Usage: FUMOUNT 0|...|7" in results["fumount-bad-nocolon.result"]
    assert "BAD NOCOLON RC=10" in results["fumount-bad-nocolon.result"]
    assert "Usage: FUMOUNT 0|...|7" in results["fumount-bad-extra.result"]
    assert "BAD EXTRA RC=10" in results["fumount-bad-extra.result"]

    assert "FMOUNT BUSY RC=0" in results["fumount-busy-mount.result"]
    busy_eject = results["fumount-busy-eject.result"]
    if "FUMOUNT BUSY RC=0" in busy_eject or "Ejected DN0:" in busy_eject:
        raise AssertionError(
            "Busy FUMOUNT retired the handler anyway; HALT — do not treat "
            "ACTION_DIE success as a DOS guarantee. Guest output:\n"
            + busy_eject
        )
    assert "FUMOUNT BUSY RC=0" not in busy_eject
    assert "Ejected DN0:" not in busy_eject
    assert "Cannot retire DN0: handler (busy)" in busy_eject
    assert "DIR BUSY RC=0" in results["fumount-busy-dir-after.result"]
    assert "KNOWN.TXT" in results["fumount-busy-dir-after.result"].upper()
    assert "TYPE BUSY RC=0" in results["fumount-busy-type.result"]
    assert "FUJINET ADF READ PASSED" in results["fumount-busy-type.result"]
    busy_status = _status(results["fumount-busy-status.result"])
    assert busy_status[0] == 0
    assert busy_status[2] == 0
