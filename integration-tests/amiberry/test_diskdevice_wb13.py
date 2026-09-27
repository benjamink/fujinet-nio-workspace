def test_wb13_ofs_mount_without_globvec(run_amiga_case):
    """KS1.3 must mount, FUMOUNT, remount, and read DN0: without GlobVec=-1."""
    results = run_amiga_case("diskdevice-wb13-ofs")

    assert "Resident loaded: fujinet-disk.device" in results["wb13-load.result"]
    assert "Mounted slot 11 on DN0:" in results["wb13-fmount-first.result"]
    assert "FUJINET ADF READ PASSED" in results["wb13-type-first.result"]
    assert "Ejected DN0:" in results["wb13-fumount.result"]
    assert "Mounted slot 11 on DN0:" in results["wb13-fmount-second.result"]
    assert "FUJINET ADF READ PASSED" in results["wb13-type-second.result"]


def test_wb13_static_multidrive_writable_lifecycle(run_amiga_case):
    """Static DN0:/DN2: entries must support independent RW media changes."""
    results = run_amiga_case("diskdevice-wb13-multidrive")

    assert "Resident loaded: fujinet-disk.device" in results["wb13-multi-load.result"]
    assert "Mounted slot 11 on DN0:" in results["wb13-multi-dn0-mount.result"]
    assert "FUJINET ADF READ PASSED" in results["wb13-multi-dn0-type.result"]
    assert "Mounted slot 13 on DN2:" in results["wb13-multi-dn2-mount.result"]
    assert "STATUS drive=2" in results["wb13-multi-dn2-status.result"]
    assert "COPY RC=$RC" in results["wb13-multi-copy.result"]
    assert "Ejected DN2:" in results["wb13-multi-dn2-eject.result"]
    assert "Mounted slot 13 on DN2:" in results["wb13-multi-dn2-remount.result"]
    assert "FUJINET WB13 WRITE PERSISTED" in results["wb13-multi-persist.result"]
    assert "Ejected DN0:" in results["wb13-multi-dn0-eject.result"]
    assert "Ejected DN2:" in results["wb13-multi-dn2-final-eject.result"]
