def test_wb13_ofs_mount_without_globvec(run_amiga_case):
    """KS1.3 ROM OFS must mount DN0: and read its known file without GlobVec=-1."""
    # The 1.3 Mount command itself does not support a redirected output
    # handle. The marker runs only after all four preceding commands succeed.
    run_amiga_case("diskdevice-wb13-ofs")
