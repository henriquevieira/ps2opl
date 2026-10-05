import io
import logging
from pathlib import Path

import pycdlib

logger = logging.getLogger("ps2opl.iso")


def find_iso_files(
    path: str | Path,
    *,
    recursive: bool = True,
) -> list[Path]:
    """
    Localiza arquivos ISO em um diretório.

    Args:
        path:
            Diretório onde a busca será realizada.

        recursive:
            Se True, procura também nos subdiretórios.

    Returns:
        Lista de caminhos para arquivos ISO encontrados.

    Raises:
        FileNotFoundError:
            Se o diretório informado não existir.

        NotADirectoryError:
            Se o caminho informado não for um diretório.
    """

    directory = Path(path).expanduser()

    if not directory.exists():
        raise FileNotFoundError(
            f"Diretório não encontrado: {directory}"
        )

    if not directory.is_dir():
        raise NotADirectoryError(
            f"O caminho informado não é um diretório: {directory}"
        )

    iterator = directory.rglob("*") if recursive else directory.iterdir()

    iso_files = [
        file
        for file in iterator
        if file.is_file() and file.suffix.lower() == ".iso"
    ]

    return sorted(iso_files)


def read_system_cnf(iso_path: str | Path) -> str:
    """
    Lê o arquivo SYSTEM.CNF diretamente de uma imagem ISO de PlayStation 2.

    A ISO não é montada e nenhum arquivo permanente é extraído.

    Args:
        iso_path:
            Caminho para a imagem ISO.

    Returns:
        Conteúdo textual do SYSTEM.CNF.

    Raises:
        FileNotFoundError:
            Se a ISO não existir.

        IsADirectoryError:
            Se o caminho informado for um diretório.

        ValueError:
            Se SYSTEM.CNF não puder ser encontrado ou lido.
    """

    path = Path(iso_path).expanduser()

    if not path.exists():
        raise FileNotFoundError(
            f"ISO não encontrada: {path}"
        )

    if not path.is_file():
        raise IsADirectoryError(
            f"O caminho informado não é um arquivo: {path}"
        )

    logger.debug("Abrindo ISO: %s", path)

    iso = pycdlib.PyCdlib()

    try:
        iso.open(str(path))

        buffer = io.BytesIO()

        try:
            iso.get_file_from_iso_fp(
                buffer,
                iso_path="/SYSTEM.CNF;1",
            )
        except pycdlib.pycdlibexception.PyCdlibException as exc:
            raise ValueError(
                f"SYSTEM.CNF não encontrado na ISO: {path}"
            ) from exc

        raw_content = buffer.getvalue()

        if not raw_content:
            raise ValueError(
                f"SYSTEM.CNF está vazio na ISO: {path}"
            )

        content = raw_content.decode(
            "ascii",
            errors="replace",
        )

        logger.debug(
            "SYSTEM.CNF lido com sucesso: %s",
            path,
        )

        return content

    except ValueError:
        raise

    except pycdlib.pycdlibexception.PyCdlibException as exc:
        raise ValueError(
            f"Não foi possível ler a ISO: {path}"
        ) from exc

    finally:
        try:
            iso.close()
        except pycdlib.pycdlibexception.PyCdlibException:
            logger.debug(
                "Erro ao fechar ISO: %s",
                path,
                exc_info=True,
            )