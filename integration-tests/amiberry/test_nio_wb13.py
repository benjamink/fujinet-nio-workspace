from pathlib import Path


def test_wb13_cold_stock_serial_worker(run_amiga_case, amiga_evidence_root):
    """The first stock serial.device open must be performed by the worker."""
    run_amiga_case("nio-wb13-cold-serial-worker")

    host_log = Path(amiga_evidence_root, "nio-wb13-cold-serial-worker",
                    "fujinet-nio.log").read_text()
    # The first request is the clock GET, issued through the resident broker
    # after its worker opens stock serial.device. The following file-list is
    # the harness completion marker.
    assert "dev=0x45 cmd=0x01" in host_log
    assert "dev=0xFE cmd=0x02" in host_log
