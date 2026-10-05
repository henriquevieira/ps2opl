from ps2opl.system_cnf import parse_system_cnf


def test_parse_system_cnf() -> None:
    content = """
    BOOT2 = cdrom0:\\SLUS_216.61;1
    VER = 1.01
    VMODE = NTSC
    """

    result = parse_system_cnf(content)

    assert result.game_id == "SLUS_216.61"
    assert result.version == "1.01"
    assert result.video_mode == "NTSC"


def test_parse_system_cnf_pal_game() -> None:
    content = """
    BOOT2 = cdrom0:\\SLES_503.30;1
    VER = 1.00
    VMODE = PAL
    """

    result = parse_system_cnf(content)

    assert result.game_id == "SLES_503.30"
    assert result.version == "1.00"
    assert result.video_mode == "PAL"


def test_parse_system_cnf_missing_optional_values() -> None:
    content = """
    BOOT2 = cdrom0:\\SCUS_973.28;1
    """

    result = parse_system_cnf(content)

    assert result.game_id == "SCUS_973.28"
    assert result.version is None
    assert result.video_mode is None