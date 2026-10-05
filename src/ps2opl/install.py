import hashlib
import logging
import os
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ps2opl.iso import (
    MediaType,
    detect_media_type,
    read_system_cnf,
)
from ps2opl.naming import build_opl_filename
from ps2opl.storage import OPLStorage
from ps2opl.system_cnf import parse_system_cnf

logger = logging.getLogger("ps2opl.install")


FAT32_MAX_FILE_SIZE = (4 * 1024**3) - 1


class InstallMethod(str, Enum):
    ISO = "ISO"
    UL = "UL"
    
class InstallError(Exception):
    """Erro durante a instalação de um jogo."""


@dataclass(frozen=True)
class InstallPlan:
    source: Path
    destination: Path | None

    game_id: str
    title: str

    media_type: MediaType
    method: InstallMethod

    file_size: int

    requires_ul: bool


def create_install_plan(
    iso_path: str | Path,
    storage: OPLStorage,
) -> InstallPlan:
    """
    Cria um plano de instalação sem modificar nenhum arquivo.
    """

    source = Path(iso_path).expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(
            f"ISO não encontrada: {source}"
        )

    if not source.is_file():
        raise IsADirectoryError(
            f"O caminho não é um arquivo: {source}"
        )

    system_cnf = read_system_cnf(source)
    config = parse_system_cnf(system_cnf)

    if not config.game_id:
        raise ValueError(
            f"Não foi possível identificar o Game ID: {source}"
        )

    media_type = detect_media_type(source)

    size = source.stat().st_size

    requires_ul = (
        storage.is_fat32
        and size > FAT32_MAX_FILE_SIZE
    )

    if requires_ul:
        method = InstallMethod.UL
        destination = None

    else:
        method = InstallMethod.ISO

        filename = build_opl_filename(
            source,
            config.game_id,
        )

        destination = (
            storage.path
            / media_type.value
            / filename
        )

    logger.debug(
        "Plano de instalação: source=%s "
        "game_id=%s media=%s method=%s destination=%s",
        source,
        config.game_id,
        media_type.value,
        method.value,
        destination,
    )

    return InstallPlan(
        source=source,
        destination=destination,
        game_id=config.game_id,
        title=source.stem,
        media_type=media_type,
        method=method,
        file_size=size,
        requires_ul=requires_ul,
    )
    
def calculate_sha256(
    path: Path,
    *,
    progress_callback=None,
    chunk_size: int = 4 * 1024 * 1024,
) -> str:
    """
    Calcula SHA-256 com acompanhamento opcional de progresso.
    """

    digest = hashlib.sha256()
    processed = 0

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)

            processed += len(chunk)

            if progress_callback is not None:
                progress_callback(processed)

    return digest.hexdigest()

def copy_iso(
    source: Path,
    destination: Path,
    *,
    progress_callback=None,
    chunk_size: int = 4 * 1024 * 1024,
) -> None:
    """
    Copia uma ISO em blocos e garante que os dados sejam
    enviados ao dispositivo antes de retornar.
    """

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    copied = 0

    with (
        source.open("rb") as source_file,
        destination.open("xb") as destination_file,
    ):
        while chunk := source_file.read(chunk_size):
            destination_file.write(chunk)

            copied += len(chunk)

            if progress_callback is not None:
                progress_callback(copied)

        # Envia buffers do Python para o sistema operacional.
        destination_file.flush()

        # Solicita que o sistema operacional sincronize
        # os dados deste arquivo com o dispositivo.
        os.fsync(destination_file.fileno())

    shutil.copystat(
        source,
        destination,
    )

def install_iso(
    plan: InstallPlan,
    storage: OPLStorage,
    *,
    copy_progress_callback=None,
    source_hash_progress_callback=None,
    destination_hash_progress_callback=None,
) -> Path:
    """
    Executa uma instalação ISO normal.

    A função:
    - valida método;
    - verifica espaço;
    - impede sobrescrita;
    - copia a ISO;
    - valida tamanho;
    - valida SHA-256.
    """

    if plan.method != InstallMethod.ISO:
        raise InstallError(
            "O plano não utiliza instalação ISO."
        )

    if plan.destination is None:
        raise InstallError(
            "O plano não possui arquivo de destino."
        )

    source = plan.source
    destination = plan.destination

    if destination.exists():
        raise InstallError(
            f"O arquivo de destino já existe: {destination}"
        )

    if storage.free_space < plan.file_size:
        raise InstallError(
            "Espaço insuficiente no dispositivo. "
            f"Necessário: {plan.file_size} bytes; "
            f"disponível: {storage.free_space} bytes."
        )

    logger.debug(
        "Copiando ISO: %s -> %s",
        source,
        destination,
    )

    try:
        copy_iso(
            source,
            destination,
            progress_callback=copy_progress_callback,
        )

        source_size = source.stat().st_size
        destination_size = destination.stat().st_size

        if source_size != destination_size:
            raise InstallError(
                "O tamanho do arquivo copiado não corresponde "
                "ao arquivo original."
            )

        logger.debug(
            "Calculando SHA-256 da origem..."
        )

        source_hash = calculate_sha256(
            source,
            progress_callback=source_hash_progress_callback,
        )

        logger.debug(
            "Calculando SHA-256 do destino..."
        )

        destination_hash = calculate_sha256(
            destination,
            progress_callback=destination_hash_progress_callback,
        )

        if source_hash != destination_hash:
            raise InstallError(
                "Falha na verificação SHA-256."
            )

    except Exception:
        if destination.exists():
            logger.warning(
                "Removendo arquivo incompleto: %s",
                destination,
            )

            destination.unlink()

        raise

    logger.debug(
        "Instalação concluída e validada: %s",
        destination,
    )

    return destination