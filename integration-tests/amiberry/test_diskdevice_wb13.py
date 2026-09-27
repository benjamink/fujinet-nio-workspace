def test_wb13_ofs_mount_without_globvec(run_amiga_case):
    """KS1.3 must mount, FUMOUNT, remount, and read DN0: without GlobVec=-1."""
    results = run_amiga_case("diskdevice-wb13-ofs")

    assert "Resident loaded: fujinet-disk.device" in results["wb13-load.result"]
    assert "Mounted slot 11 on DN0:" in results["wb13-fmount-first.result"]
    assert "FUJINET ADF READ PASSED" in results["wb13-type-first.result"]
    assert "Ejected DN0:" in results["wb13-fumount.result"]
    assert "Mounted slot 11 on DN0:" in results["wb13-fmount-second.result"]
    assert "FUJINET ADF READ PASSED" in results["wb13-type-second.result"]
