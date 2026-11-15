import pytest


def second_fumount_absent(kind, unit, result, pytestconfig):
    """A second FUMOUNT of a unit the first already unmounted.

    Where handlers can exit (WB3.2) the first FUMOUNT removes the DOS node, so
    the second finds none and, since nio-core-apps 94bf0d85, treats that as
    already removed: RC=0 and a note. Earlier Workbenches park the handler
    instead (the node stays), so the second FUMOUNT reports the unit is not
    mounted and fails with RC=10.
    """
    if pytestconfig.getoption("--amiga-env").startswith("wb32"):
        assert f"{kind} SECOND FUMOUNT RC=0" in result
        assert f"{unit} no DOS entry to remove" in result
    else:
        assert f"{kind} SECOND FUMOUNT RC=0" not in result
        assert f"{unit} is not mounted" in result


@pytest.mark.parametrize("installation", ["serial", "native"])
def test_fmount_fumount_persisted_dd_hd_restore(run_amiga_case, installation, pytestconfig):
    results = run_amiga_case("diskdevice-fmount-restore", installation=installation)

    assert "DD FMOUNT RC=0" in results["restore-dd-mount.result"]
    assert "KNOWN.TXT" in results["restore-dd-before-dir.result"].upper()
    assert "DD DIR BEFORE RC=0" in results["restore-dd-before-dir.result"]
    assert "FUJINET ADF READ PASSED" in results["restore-dd-before-type.result"]
    assert "DD TYPE BEFORE RC=0" in results["restore-dd-before-type.result"]

    assert "HD FMOUNT RC=0" in results["restore-hd-mount.result"]
    assert "HD.TXT" in results["restore-hd-before-dir.result"].upper()
    assert "HD DIR BEFORE RC=0" in results["restore-hd-before-dir.result"]
    assert "FUJINET HD ADF READ PASSED" in results["restore-hd-before-type.result"]
    assert "HD TYPE BEFORE RC=0" in results["restore-hd-before-type.result"]

    assert "FMOUNTRESTORE unit=0 slot=11 mode=RO" in results["restore-startup.result"]
    assert "FMOUNTRESTORE unit=1 slot=14 mode=RO" in results["restore-startup.result"]
    assert "FMOUNTRESTORE restored=2" in results["restore-startup.result"]
    assert "RESTORE RC=0" in results["restore-startup.result"]

    assert "KNOWN.TXT" in results["restore-dd-after-dir.result"].upper()
    assert "DD DIR AFTER RC=0" in results["restore-dd-after-dir.result"]
    assert "FUJINET ADF READ PASSED" in results["restore-dd-after-type.result"]
    assert "DD TYPE AFTER RC=0" in results["restore-dd-after-type.result"]
    assert "HD.TXT" in results["restore-hd-after-dir.result"].upper()
    assert "HD DIR AFTER RC=0" in results["restore-hd-after-dir.result"]
    assert "FUJINET HD ADF READ PASSED" in results["restore-hd-after-type.result"]
    assert "HD TYPE AFTER RC=0" in results["restore-hd-after-type.result"]

    assert "DD FUMOUNT RC=0" in results["restore-dd-fumount.result"]
    second_fumount_absent("DD", "DN0:", results["restore-dd-absent.result"], pytestconfig)
    assert "HD FUMOUNT RC=0" in results["restore-hd-fumount.result"]
    second_fumount_absent("HD", "DN1:", results["restore-hd-absent.result"], pytestconfig)
    assert results["_mappings"] == "01" + "00" * 16


@pytest.mark.parametrize("installation", ["serial", "native"])
def test_invalid_persisted_mapping_fails_without_creating_node(run_amiga_case, installation):
    results = run_amiga_case("diskdevice-fmount-restore-invalid", installation=installation)

    assert "FMOUNTRESTORE unit=0 slot=99 rc=" in results["restore-invalid.result"]
    assert "RESTORE INVALID RC=0" not in results["restore-invalid.result"]
    assert "DN0 type=0" not in results["restore-invalid-dos.result"]
