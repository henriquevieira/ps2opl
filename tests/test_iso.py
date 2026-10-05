from pathlib import Path

import pytest

from ps2opl.iso import find_iso_files


def test_find_iso_files(tmp_path: Path) -> None:
    (tmp_path / "game1.iso").touch()
    (tmp_path / "game2.ISO").touch()
    (tmp_path / "readme.txt").touch()

    result = find_iso_files(tmp_path)

    assert result == [
        tmp_path / "game1.iso",
        tmp_path / "game2.ISO",
    ]


def test_find_iso_files_recursively(tmp_path: Path) -> None:
    dvd_directory = tmp_path / "DVD"
    dvd_directory.mkdir()

    (tmp_path / "game1.iso").touch()
    (dvd_directory / "game2.iso").touch()

    result = find_iso_files(tmp_path)

    assert result == [
        dvd_directory / "game2.iso",
        tmp_path / "game1.iso",
    ]


def test_find_iso_files_without_recursion(tmp_path: Path) -> None:
    dvd_directory = tmp_path / "DVD"
    dvd_directory.mkdir()

    (tmp_path / "game1.iso").touch()
    (dvd_directory / "game2.iso").touch()

    result = find_iso_files(
        tmp_path,
        recursive=False,
    )

    assert result == [
        tmp_path / "game1.iso",
    ]


def test_find_iso_files_empty_directory(tmp_path: Path) -> None:
    result = find_iso_files(tmp_path)

    assert result == []


def test_find_iso_files_directory_not_found(tmp_path: Path) -> None:
    directory = tmp_path / "does-not-exist"

    with pytest.raises(FileNotFoundError):
        find_iso_files(directory)


def test_find_iso_files_path_is_file(tmp_path: Path) -> None:
    file = tmp_path / "game.iso"
    file.touch()

    with pytest.raises(NotADirectoryError):
        find_iso_files(file)