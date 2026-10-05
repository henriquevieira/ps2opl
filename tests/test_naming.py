from ps2opl.naming import (
    build_opl_filename,
    get_game_title,
    sanitize_opl_title,
)


def test_get_game_title() -> None:
    result = get_game_title(
        "Ben 10 - Protector of Earth (USA).iso"
    )

    assert result == "Ben 10 - Protector of Earth"


def test_get_game_title_without_region() -> None:
    result = get_game_title(
        "Shadow of the Colossus.iso"
    )

    assert result == "Shadow of the Colossus"


def test_get_game_title_multilanguage_region() -> None:
    result = get_game_title(
        "Game Name (USA, En,Ja,Fr,De,Es).iso"
    )

    assert result == "Game Name"


def test_sanitize_opl_title() -> None:
    result = sanitize_opl_title(
        "Game: Special / Edition"
    )

    assert result == "Game- Special - Edition"


def test_build_opl_filename() -> None:
    result = build_opl_filename(
        "Ben 10 - Protector of Earth (USA).iso",
        "SLUS_216.61",
    )

    assert (
        result
        == "SLUS_216.61.Ben 10 - Protector of Earth.iso"
    )
    
def test_get_game_title_already_opl_named() -> None:
    result = get_game_title(
        "SLUS_216.61.Ben 10 - Protector of Earth.iso"
    )

    assert result == "Ben 10 - Protector of Earth"