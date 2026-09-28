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
    assert "Ejected DN2:" in results["wb13-multi-dn2-finale.result"]


def test_wb13_secondary_readonly_lifecycle(run_amiga_case):
    """A secondary read-only unit must survive eject/reinsert beside DN0:."""
    results = run_amiga_case("diskdevice-wb13-secondary-ro")

    assert "FUJINET ADF READ PASSED" in results["w13ro-dn0t.result"]
    assert "FUJINET ADF READ PASSED" in results["w13ro-dn2t.result"]
    assert "Ejected DN2:" in results["w13ro-eject.result"]
    assert "Mounted slot 11 on DN2:" in results["w13ro-remnt.result"]
    assert "FUJINET ADF READ PASSED" in results["w13ro-remntt.result"]


def test_wb13_secondary_writable_lifecycle_without_dn0(run_amiga_case):
    """Separate write-back failure from concurrent-unit behaviour."""
    results = run_amiga_case("diskdevice-wb13-secondary-rw-alone")

    assert "COPY RC=$RC" in results["w13rw-copy.result"]
    assert "Ejected DN2:" in results["w13rw-eject.result"]
    assert "Mounted slot 13 on DN2:" in results["w13rw-remnt.result"]
    assert "FUJINET WB13 WRITE PERSISTED" in results["w13rw-persist.result"]
