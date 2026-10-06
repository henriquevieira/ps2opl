from pathlib import Path

import pytest

from ps2opl import ul
from ps2opl.iso import MediaType
from ps2opl.ul import (
    UL_MEDIA_CD,
    UL_MEDIA_DVD,
    UL_RECORD_SIZE,
    build_ul_record,
    parse_ul_record,
)


def test_build_ul_record_dvd() -> None:
    title = b"Ben 10 - Ultimate Alien"

    record = build_ul_record(
        title="Ben 10 - Ultimate Alien",
        game_id="SLUS_219.38",
        parts=5,
        media_type=MediaType.DVD,
    )

    assert len(record) == UL_RECORD_SIZE

    assert record[0x00:0x20] == (
        title
        + b"\x00" * (32 - len(title))
    )

    assert record[0x20:0x23] == b"ul."

    assert (
        record[0x23:0x2F]
        == b"SLUS_219.38\x00"
    )

    assert record[0x2F] == 5
    assert record[0x30] == UL_MEDIA_DVD
    assert record[0x31:0x35] == b"\x00" * 4
    assert record[0x35] == 0x08
    assert record[0x36:0x40] == b"\x00" * 10
    
    
def test_build_ul_record_cd() -> None:
    record = build_ul_record(
        title="Example",
        game_id="SLUS_123.45",
        parts=1,
        media_type=MediaType.CD,
    )

    assert record[0x30] == UL_MEDIA_CD
    
def test_ul_record_round_trip() -> None:
    record = build_ul_record(
        title="Teen Titans",
        game_id="SLUS_211.83",
        parts=2,
        media_type=MediaType.DVD,
    )

    game = parse_ul_record(record)

    assert game.title == "Teen Titans"
    assert game.game_id == "SLUS_211.83"
    assert game.parts == 2
    assert game.media_type == MediaType.DVD
    
def test_write_ul_parts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ul,
        "UL_PART_SIZE",
        10,
    )

    source = tmp_path / "game.iso"
    source.write_bytes(
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )

    plan = ul.create_ul_install_plan(
        source=source,
        storage_path=tmp_path,
        title="Test Game",
        game_id="SLUS_123.45",
        media_type=MediaType.DVD,
    )

    parts = ul.write_ul_parts(plan)

    assert len(parts) == 3

    assert parts[0].read_bytes() == b"ABCDEFGHIJ"
    assert parts[1].read_bytes() == b"KLMNOPQRST"
    assert parts[2].read_bytes() == b"UVWXYZ"
    
def test_ul_parts_sha256(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ul,
        "UL_PART_SIZE",
        10,
    )

    source = tmp_path / "game.iso"
    source.write_bytes(
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )

    plan = ul.create_ul_install_plan(
        source=source,
        storage_path=tmp_path,
        title="Test Game",
        game_id="SLUS_123.45",
        media_type=MediaType.DVD,
    )

    parts = ul.write_ul_parts(plan)

    source_hash = ul.calculate_file_sha256(
        source
    )

    parts_hash = ul.calculate_ul_parts_sha256(
        parts
    )

    assert source_hash == parts_hash
    
def test_install_ul_parts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ul,
        "UL_PART_SIZE",
        10,
    )

    source = tmp_path / "game.iso"

    source.write_bytes(
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )

    storage = tmp_path / "storage"
    storage.mkdir()

    plan = ul.create_ul_install_plan(
        source=source,
        storage_path=storage,
        title="Test Game",
        game_id="SLUS_123.45",
        media_type=MediaType.DVD,
    )

    parts = ul.install_ul_parts(
        plan,
        free_space=1024,
    )

    assert len(parts) == 3

    assert parts[0].read_bytes() == b"ABCDEFGHIJ"
    assert parts[1].read_bytes() == b"KLMNOPQRST"
    assert parts[2].read_bytes() == b"UVWXYZ"

    assert (
        ul.calculate_file_sha256(source)
        == ul.calculate_ul_parts_sha256(parts)
    )
    
def test_install_ul_parts_insufficient_space(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ul,
        "UL_PART_SIZE",
        10,
    )

    source = tmp_path / "game.iso"
    source.write_bytes(b"A" * 100)

    storage = tmp_path / "storage"
    storage.mkdir()

    plan = ul.create_ul_install_plan(
        source=source,
        storage_path=storage,
        title="Test Game",
        game_id="SLUS_123.45",
        media_type=MediaType.DVD,
    )

    try:
        ul.install_ul_parts(
            plan,
            free_space=50,
        )

    except ul.ULInstallError:
        pass

    else:
        raise AssertionError(
            "ULInstallError deveria ter sido lançado."
        )

    assert not any(
        storage.glob("ul.*")
    )
    
def test_install_ul_parts_does_not_overwrite(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ul,
        "UL_PART_SIZE",
        10,
    )

    source = tmp_path / "game.iso"
    source.write_bytes(b"A" * 20)

    storage = tmp_path / "storage"
    storage.mkdir()

    plan = ul.create_ul_install_plan(
        source=source,
        storage_path=storage,
        title="Test Game",
        game_id="SLUS_123.45",
        media_type=MediaType.DVD,
    )

    existing = plan.part_paths[0]

    existing.write_bytes(
        b"DO NOT OVERWRITE"
    )

    with pytest.raises(
        ul.ULInstallError,
        match="Já existem partes UL",
    ):
        ul.install_ul_parts(
            plan,
            free_space=1024,
        )

    assert (
        existing.read_bytes()
        == b"DO NOT OVERWRITE"
    )
    
def test_install_ul_progress_callbacks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ul,
        "UL_PART_SIZE",
        10,
    )

    source = tmp_path / "game.iso"
    source.write_bytes(
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )

    storage = tmp_path / "storage"
    storage.mkdir()

    plan = ul.create_ul_install_plan(
        source=source,
        storage_path=storage,
        title="Test Game",
        game_id="SLUS_123.45",
        media_type=MediaType.DVD,
    )

    copy_progress = []
    source_progress = []
    parts_progress = []

    ul.install_ul_parts(
        plan,
        free_space=1024,
        copy_progress_callback=copy_progress.append,
        source_hash_progress_callback=source_progress.append,
        parts_hash_progress_callback=parts_progress.append,
    )

    assert copy_progress[-1] == len(
        source.read_bytes()
    )

    assert source_progress[-1] == len(
        source.read_bytes()
    )

    assert parts_progress[-1] == len(
        source.read_bytes()
    )
    
def test_register_first_ul_game(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ul,
        "UL_PART_SIZE",
        10,
    )

    source = tmp_path / "game.iso"
    source.write_bytes(
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )

    storage = tmp_path / "storage"
    storage.mkdir()

    plan = ul.create_ul_install_plan(
        source=source,
        storage_path=storage,
        title="Test Game",
        game_id="SLUS_123.45",
        media_type=MediaType.DVD,
    )

    parts = ul.install_ul_parts(
        plan,
        free_space=1024,
    )

    assert len(parts) == 3

    cfg_path = ul.register_ul_game(plan)

    assert cfg_path.exists()
    assert cfg_path.stat().st_size == 64

    games = ul.read_ul_cfg(cfg_path)

    assert len(games) == 1
    assert games[0].title == "Test Game"
    assert games[0].game_id == "SLUS_123.45"
    assert games[0].parts == 3
    assert games[0].media_type == MediaType.DVD
    
def test_register_ul_game_rejects_duplicate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ul,
        "UL_PART_SIZE",
        10,
    )

    source = tmp_path / "game.iso"
    source.write_bytes(
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )

    storage = tmp_path / "storage"
    storage.mkdir()

    plan = ul.create_ul_install_plan(
        source=source,
        storage_path=storage,
        title="Test Game",
        game_id="SLUS_123.45",
        media_type=MediaType.DVD,
    )

    ul.install_ul_parts(
        plan,
        free_space=1024,
    )

    ul.register_ul_game(plan)

    original = plan.cfg_path.read_bytes()

    with pytest.raises(
        ul.ULInstallError,
        match="já está",
    ):
        ul.register_ul_game(plan)

    assert plan.cfg_path.read_bytes() == original
    assert plan.cfg_path.stat().st_size == 64
    
def test_ul_crc32_known_opl_vector() -> None:
    assert (
        ul.ul_crc32(
            "Ben 10 - Ultimate Alien - Cosmic"
        )
        == 0xEA4144B6
    )