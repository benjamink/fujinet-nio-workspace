def test_fboot_activates_configured_default_adf(run_amiga_case):
    results = run_amiga_case("diskdevice-default-disk")

    assert "LOAD RC=0" in results["default-load.result"]
    assert "Default disk active on DN0: (FFS, DD)" in results["default-fboot.result"]
    assert "FBOOT RC=0" in results["default-fboot.result"]
    assert "DEFAULT.TXT" in results["default-dir.result"].upper()
    assert "DIR RC=0" in results["default-dir.result"]
    assert "FUJINET DEFAULT DISK PASSED" in results["default-type.result"]
    assert "TYPE RC=0" in results["default-type.result"]
