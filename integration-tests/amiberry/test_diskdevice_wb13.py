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


def test_wb13_static_drives_cross_copy_and_eject_independently(run_amiga_case):
    """WB1.3 static drives must copy via DH0: and each other, then eject."""
    results = run_amiga_case("diskdevice-wb13-cross-copy")

    assert "Mounted slot 13 on DN0:" in results["w13xc-dn0m.result"]
    assert "Mounted slot 20 on DN2:" in results["w13xc-dn2m.result"]
    assert "COPY RC=$RC" in results["w13xc-to-dn2.result"]
    assert "COPY RC=$RC" in results["w13xc-to-dn0.result"]
    assert "COPY RC=$RC" in results["w13xc-to-dh0.result"]
    assert "FUJINET WB13 CROSS COPY" in results["w13xc-dh0.result"]
    assert "FUJINET WB13 CROSS COPY" in results["w13xc-dn0.result"]
    assert "FUJINET WB13 CROSS COPY" in results["w13xc-dn2.result"]
    assert "Ejected DN0:" in results["w13xc-dn0e.result"]
    assert "Ejected DN2:" in results["w13xc-dn2e.result"]


def test_wb13_all_static_units_mount_and_read(run_amiga_case):
    """Every installed WB1.3 MountList unit DN0: through DN7: can read media."""
    results = run_amiga_case("diskdevice-wb13-all-units")

    assert "Resident loaded: fujinet-disk.device" in results["w13u-load.result"]
    for unit in range(8):
        stem = f"w13u-dn{unit}"
        assert f"Mounted slot 11 on DN{unit}:" in results[f"{stem}m.result"]
        assert "FUJINET ADF READ PASSED" in results[f"{stem}t.result"]


def test_wb13_readonly_media_reports_protection(run_amiga_case):
    """A read-only catalogue mount must present protected media to trackdisk."""
    results = run_amiga_case("diskdevice-wb13-readonly")

    assert "Mounted slot 11 on DN0:" in results["w13wp-mount.result"]
    assert "STATUS drive=0" in results["w13wp-status.result"]
    assert "protected=1" in results["w13wp-status.result"]
    assert "FUJINET ADF READ PASSED" in results["w13wp-known.result"]
