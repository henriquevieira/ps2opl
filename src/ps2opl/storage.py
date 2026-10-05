import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("ps2opl.storage")


REQUIRED_OPL_DIRECTORIES = (
    "CD",
    "DVD",
)

OPTIONAL_OPL_DIRECTORIES = (
    "ART",
    "CFG",
    "CHT",
    "VMC",
    "THM",
    "LNG",
    "APPS",
)


@dataclass(frozen=True)
class OPLStorage:
    path: Path
    filesystem: str | None
    total_space: int
    used_space: int
    free_space: int
    required_directories: dict[str, bool]
    optional_directories: dict[str, bool]

    @property
    def is_valid(self) -> bool:
        """
        Indica se o dispositivo possui a estrutura mínima
        necessária para armazenamento de jogos OPL.
        """
        return all(self.required_directories.values())

    @property
    def is_fat32(self) -> bool:
        """
        Indica se o filesystem é FAT32.
        """
        if self.filesystem is None:
            return False

        return self.filesystem.lower() in {
            "vfat",
            "fat32",
            "msdos",
        }


def get_filesystem(path: Path) -> str | None:
    """
    Obtém o filesystem correspondente ao caminho informado.

    No Linux utiliza o comando findmnt.
    """

    try:
        result = subprocess.run(
            [
                "findmnt",
                "-no",
                "FSTYPE",
                "--target",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning(
            "Não foi possível detectar o filesystem de %s",
            path,
        )
        return None

    filesystem = result.stdout.strip()

    return filesystem or None


def inspect_opl_storage(
    path: str | Path,
) -> OPLStorage:
    """
    Inspeciona um diretório ou dispositivo montado e verifica
    sua estrutura OPL.

    A função não modifica nenhum arquivo.

    Args:
        path:
            Caminho onde o dispositivo está montado.

    Returns:
        Informações sobre o armazenamento OPL.

    Raises:
        FileNotFoundError:
            Se o caminho não existir.

        NotADirectoryError:
            Se o caminho não for um diretório.
    """

    storage_path = Path(path).expanduser().resolve()

    if not storage_path.exists():
        raise FileNotFoundError(
            f"Caminho não encontrado: {storage_path}"
        )

    if not storage_path.is_dir():
        raise NotADirectoryError(
            f"O caminho não é um diretório: {storage_path}"
        )

    logger.debug(
        "Inspecionando armazenamento OPL: %s",
        storage_path,
    )

    usage = shutil.disk_usage(storage_path)

    filesystem = get_filesystem(storage_path)

    required = {
        directory: (storage_path / directory).is_dir()
        for directory in REQUIRED_OPL_DIRECTORIES
    }

    optional = {
        directory: (storage_path / directory).is_dir()
        for directory in OPTIONAL_OPL_DIRECTORIES
    }

    storage = OPLStorage(
        path=storage_path,
        filesystem=filesystem,
        total_space=usage.total,
        used_space=usage.used,
        free_space=usage.free,
        required_directories=required,
        optional_directories=optional,
    )

    logger.debug(
        "Armazenamento analisado: filesystem=%s total=%d "
        "free=%d valid=%s",
        filesystem,
        usage.total,
        usage.free,
        storage.is_valid,
    )

    return storage