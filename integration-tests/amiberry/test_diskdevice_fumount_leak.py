import re


def _cycles(text):
    """Return [(total_free, opencnt)] per cycle from Avail/devopencnt output."""
    cycles = []
    for block in re.split(r"^CYCLE \d+\n", text, flags=re.M)[1:]:
        total = re.search(r"^total\s+(\d+)", block, re.M | re.I)
        opencnt = re.search(r"opencnt=(\d+)", block)
        cycles.append((int(total.group(1)), int(opencnt.group(1))))
    return cycles


def test_fumount_cycles_do_not_leak(run_amiga_case):
    results = run_amiga_case("diskdevice-fumount-leak")

    assert "LOAD RC=0" in results["leak-load.result"]
    ops = results["leak-ops.result"]
    for cycle in range(1, 13):
        assert f"C{cycle} FMOUNT RC=0" in ops
        assert f"C{cycle} COPY RC=0" in ops
        assert f"C{cycle} FUMOUNT RC=0" in ops

    cycles = _cycles(results["leak-cycles.result"])
    assert len(cycles) == 13
    print("cycle free opencnt:", cycles)
    # The first cycle warms caches (and on WB3.1 starts the one handler that
    # FUMOUNT parks for reuse); every later cycle must reuse it, not add more.
    first_opencnt = cycles[1][1]
    assert first_opencnt <= 1
    assert all(opencnt == first_opencnt for _, opencnt in cycles[1:])
    assert cycles[1][0] - cycles[-1][0] < 4096
