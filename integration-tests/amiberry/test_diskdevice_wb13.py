def test_wb13_ofs_mount_without_globvec(run_amiga_case):
    """KS1.3 must mount, FUMOUNT, remount, and read DN0: without GlobVec=-1."""
    results = run_amiga_case("diskdevice-wb13-ofs")

    assert "Resident loaded: fujinet-disk.device" in results["wb13-load.result"]
    assert "Mounted slot 11 on DO0: (DD, OFS)" in results["wb13-fmount-first.result"]
    assert "FUJINET ADF READ PASSED" in results["wb13-type-first.result"]
    assert "Ejected DO0:" in results["wb13-fumount.result"]
    assert "Mounted slot 11 on DO0: (DD, OFS)" in results["wb13-fmount-second.result"]
    assert "FUJINET ADF READ PASSED" in results["wb13-type-second.result"]


def test_wb13_static_multidrive_writable_lifecycle(run_amiga_case):
    """Static DN0:/DN2: entries must support independent RW media changes."""
    results = run_amiga_case("diskdevice-wb13-multidrive")

    assert "Resident loaded: fujinet-disk.device" in results["wb13-multi-load.result"]
    assert "Mounted slot 11 on DO0: (DD, OFS)" in results["wb13-multi-dn0-mount.result"]
    assert "FUJINET ADF READ PASSED" in results["wb13-multi-dn0-type.result"]
    assert "Mounted slot 13 on DO1: (DD, OFS)" in results["wb13-multi-dn2-mount.result"]
    assert "STATUS drive=5" in results["wb13-multi-dn2-status.result"]
    assert "COPY RC=$RC" in results["wb13-multi-copy.result"]
    assert "Ejected DO1:" in results["wb13-multi-dn2-eject.result"]
    assert "Mounted slot 13 on DO1: (DD, OFS)" in results["wb13-multi-dn2-remount.result"]
    assert "FUJINET WB13 WRITE PERSISTED" in results["wb13-multi-persist.result"]
    assert "Ejected DO0:" in results["wb13-multi-dn0-eject.result"]
    assert "Ejected DO1:" in results["wb13-multi-dn2-finale.result"]


def test_wb13_secondary_readonly_lifecycle(run_amiga_case):
    """A secondary read-only unit must survive eject/reinsert beside DN0:."""
    results = run_amiga_case("diskdevice-wb13-secondary-ro")

    assert "FUJINET ADF READ PASSED" in results["w13ro-dn0t.result"]
    assert "FUJINET ADF READ PASSED" in results["w13ro-dn2t.result"]
    assert "Ejected DO1:" in results["w13ro-eject.result"]
    assert "Mounted slot 11 on DO1: (DD, OFS)" in results["w13ro-remnt.result"]
    assert "FUJINET ADF READ PASSED" in results["w13ro-remntt.result"]


def test_wb13_secondary_writable_lifecycle_without_dn0(run_amiga_case):
    """Separate write-back failure from concurrent-unit behaviour."""
    results = run_amiga_case("diskdevice-wb13-secondary-rw-alone")

    assert "COPY RC=$RC" in results["w13rw-copy.result"]
    assert "Ejected DO1:" in results["w13rw-eject.result"]
    assert "Mounted slot 13 on DO1: (DD, OFS)" in results["w13rw-remnt.result"]
    assert "FUJINET WB13 WRITE PERSISTED" in results["w13rw-persist.result"]


def test_wb13_static_drives_cross_copy_and_eject_independently(run_amiga_case):
    """WB1.3 static drives must copy via DH0: and each other, then eject."""
    results = run_amiga_case("diskdevice-wb13-cross-copy")

    assert "Mounted slot 13 on DO0: (DD, OFS)" in results["w13xc-dn0m.result"]
    assert "Mounted slot 20 on DO1: (DD, OFS)" in results["w13xc-dn2m.result"]
    assert "COPY RC=$RC" in results["w13xc-to-dn2.result"]
    assert "COPY RC=$RC" in results["w13xc-to-dn0.result"]
    assert "COPY RC=$RC" in results["w13xc-to-dh0.result"]
    assert "FUJINET WB13 CROSS COPY" in results["w13xc-dh0.result"]
    assert "FUJINET WB13 CROSS COPY" in results["w13xc-dn0.result"]
    assert "FUJINET WB13 CROSS COPY" in results["w13xc-dn2.result"]
    assert "Ejected DO0:" in results["w13xc-dn0e.result"]
    assert "Ejected DO1:" in results["w13xc-dn2e.result"]


def test_wb13_all_static_ofs_endpoints_mount_and_read(run_amiga_case):
    """Both installed WB1.3 DD/OFS endpoints can read media concurrently."""
    results = run_amiga_case("diskdevice-wb13-all-units")

    assert "Resident loaded: fujinet-disk.device" in results["w13u-load.result"]
    for unit in range(2):
        stem = f"w13u-dn{unit}"
        assert f"Mounted slot 11 on DO{unit}: (DD, OFS)" in results[f"{stem}m.result"]
        assert "FUJINET ADF READ PASSED" in results[f"{stem}t.result"]


def test_wb13_readonly_media_reports_protection(run_amiga_case):
    """A read-only catalogue mount must present protected media to trackdisk."""
    results = run_amiga_case("diskdevice-wb13-readonly")

    assert "Mounted slot 11 on DO0: (DD, OFS)" in results["w13wp-mount.result"]
    assert "STATUS drive=4" in results["w13wp-status.result"]
    assert "protected=1" in results["w13wp-status.result"]
    assert "FUJINET ADF READ PASSED" in results["w13wp-known.result"]


def test_wb13_mixed_dd_and_hd_static_handlers(run_amiga_case):
    """Mixed WB1.3 MountList supports simultaneous DD and HD read/write media."""
    results = run_amiga_case("diskdevice-wb13-mixed-hd")

    assert "Resident loaded: fujinet-disk.device" in results["wb13mix-load.result"]
    assert "Mounted slot 13 on DO0: (DD, OFS)" in results["wb13mix-dd-mount.result"]
    assert "Mounted slot 21 on HO0: (HD, OFS)" in results["wb13mix-hd-mount.result"]
    assert "STATUS drive=4" in results["wb13mix-dd-status.result"]
    assert "STATUS drive=6" in results["wb13mix-hd-status.result"]
    assert "FUJINET WRITABLE BASE" in results["wb13mix-hd-copy.result"]
    assert "FUJINET WRITABLE HD BASE" in results["wb13mix-dd-copy.result"]
    assert "Ejected HO0:" in results["wb13mix-hd-eject.result"]
    assert "Mounted slot 21 on HO0: (HD, OFS)" in results["wb13mix-hd-remount.result"]
    assert "FUJINET WRITABLE BASE" in results["wb13mix-hd-persist.result"]


def test_wb13_failed_secondary_mount_preserves_primary_media(run_amiga_case):
    """A bad static DN2: mount must not disrupt a usable DN0: medium."""
    results = run_amiga_case("diskdevice-wb13-failed-secondary-mount")

    assert "Mounted slot 11 on DO0: (DD, OFS)" in results["w13fail-dn0-mount.result"]
    assert "INVALID REJECTED" in results["w13fail-dn2-invalid.result"]
    assert "FUJINET ADF READ PASSED" in results["w13fail-dn0-type.result"]
    assert "STATUS drive=4" in results["w13fail-dn0-status.result"]
    assert "absent=0" in results["w13fail-dn0-status.result"]


def test_wb13_mount_times_out_against_stalled_external_peer(run_amiga_case):
    """WB1.3 command-clock client must return a bounded mount failure."""
    results = run_amiga_case("diskdevice-stalled-external-peer")

    assert "STALLED PEER TIMEOUT RC=20" in results["stalled-peer-timeout.result"]
    assert results["fmount.result"].strip() == ""
