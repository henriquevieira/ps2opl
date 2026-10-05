from pathlib import Path

import pytest

from ps2opl.storage import inspect_opl_storage


def test_valid_opl_storage(tmp_path: Path) -> None:
    (tmp_path / "CD").mkdir()
    (tmp_path / "DVD").mkdir()

    storage = inspect_opl_storage(tmp_path)

    assert storage.is_valid
    assert storage.required_directories["CD"]
    assert storage.required_directories["DVD"]


def test_invalid_opl_storage_without_cd(
    tmp_path: Path,
) -> None:
    (tmp_path / "DVD").mkdir()

    storage = inspect_opl_storage(tmp_path)

    assert not storage.is_valid
    assert not storage.required_directories["CD"]
    assert storage.required_directories["DVD"]


def test_invalid_opl_storage_without_dvd(
    tmp_path: Path,
) -> None:
    (tmp_path / "CD").mkdir()

    storage = inspect_opl_storage(tmp_path)

    assert not storage.is_valid
    assert storage.required_directories["CD"]
    assert not storage.required_directories["DVD"]


def test_optional_directories(
    tmp_path: Path,
) -> None:
    (tmp_path / "CD").mkdir()
    (tmp_path / "DVD").mkdir()
    (tmp_path / "ART").mkdir()
    (tmp_path / "VMC").mkdir()

    storage = inspect_opl_storage(tmp_path)

    assert storage.optional_directories["ART"]
    assert storage.optional_directories["VMC"]
    assert not storage.optional_directories["CFG"]


def test_storage_not_found(tmp_path: Path) -> None:
    path = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        inspect_opl_storage(path)


def test_storage_path_is_file(tmp_path: Path) -> None:
    path = tmp_path / "file"
    path.touch()

    with pytest.raises(NotADirectoryError):
        inspect_opl_storage(path)