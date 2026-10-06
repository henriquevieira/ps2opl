import hashlib
import math
import os
from dataclasses import dataclass
from pathlib import Path

from ps2opl.iso import MediaType

UL_RECORD_SIZE = 64
UL_PART_SIZE = 1024 * 1024 * 1024
UL_MEDIA_CD = 0x12
UL_MEDIA_DVD = 0x14
UL_TITLE_MAX_BYTES = 32

@dataclass(frozen=True)
class ULGame:
    """
    Representa uma entrada do arquivo ul.cfg.
    """

    title: str
    game_id: str
    parts: int
    media_type: MediaType

@dataclass(frozen=True)
class ULInstallPlan:
    """
    Plano para instalação de uma ISO no formato UL/USBExtreme.
    """

    source: Path
    storage_path: Path

    title: str
    game_id: str

    media_type: MediaType

    file_size: int
    part_size: int
    part_count: int

    crc32: int

    part_paths: tuple[Path, ...]

    cfg_path: Path

class ULInstallError(Exception):
    """Erro durante uma instalação UL/USBExtreme."""

def read_ul_records(
    path: str | Path,
) -> list[bytes]:
    """
    Lê os registros brutos de um arquivo ul.cfg.

    Nenhuma modificação é realizada.
    """

    cfg_path = Path(path).expanduser()

    if not cfg_path.exists():
        raise FileNotFoundError(
            f"ul.cfg não encontrado: {cfg_path}"
        )

    if not cfg_path.is_file():
        raise IsADirectoryError(
            f"O caminho não é um arquivo: {cfg_path}"
        )

    data = cfg_path.read_bytes()

    if not data:
        return []

    if len(data) % UL_RECORD_SIZE != 0:
        raise ValueError(
            "Tamanho inválido de ul.cfg: "
            f"{len(data)} bytes não é múltiplo de "
            f"{UL_RECORD_SIZE}."
        )

    return [
        data[offset : offset + UL_RECORD_SIZE]
        for offset in range(
            0,
            len(data),
            UL_RECORD_SIZE,
        )
    ]

def format_hex_record(record: bytes) -> str:
    """
    Gera representação hexadecimal de um registro UL.
    """

    return " ".join(
        f"{byte:02X}"
        for byte in record
    )
    
def ul_crc32(text: str) -> int:
    """
    Calcula o CRC utilizado pelo formato UL/USBExtreme.

    Implementação compatível com iso2opl/opl2iso do
    Open PS2 Loader.
    """

    try:
        data = text.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(
            "UL title must contain only ASCII characters."
        ) from exc

    table = [0] * 256

    crc = 0

    for table_index in range(256):
        crc = (table_index << 24) & 0xFFFFFFFF

        for _ in range(8):
            if crc & 0x80000000:
                crc = (
                    crc << 1
                ) & 0xFFFFFFFF
            else:
                crc = (
                    (crc << 1)
                    ^ 0x04C11DB7
                ) & 0xFFFFFFFF

        table[255 - table_index] = crc

    # IMPORTANTE:
    # não reinicializar crc aqui.
    #
    # A implementação original mantém o valor deixado
    # pelo último ciclo de construção da tabela.

    for byte in data + b"\x00":
        index = (
            byte
            ^ ((crc >> 24) & 0xFF)
        )

        crc = (
            table[index]
            ^ (
                (crc << 8)
                & 0xFFFFFF00
            )
        ) & 0xFFFFFFFF

    return crc

def build_ul_part_name(
    title: str,
    game_id: str,
    part: int,
) -> str:
    """
    Gera o nome de uma parte UL.

    Exemplo:

        ul.1234ABCD.SLUS_219.38.00
    """

    ul_title = normalize_ul_title(title)
    crc = ul_crc32(ul_title)

    return (
        f"ul.{crc:08X}."
        f"{game_id}."
        f"{part:02d}"
    )
    
def calculate_ul_parts(
    file_size: int,
) -> int:
    """
    Calcula quantas partes de até 1 GiB são necessárias.
    """

    if file_size <= 0:
        raise ValueError(
            "O tamanho da ISO deve ser maior que zero."
        )

    return math.ceil(
        file_size / UL_PART_SIZE
    )
    
def create_ul_install_plan(
    source: Path,
    storage_path: Path,
    title: str,
    game_id: str,
    media_type: MediaType,
) -> ULInstallPlan:
    """
    Cria um plano de instalação UL sem modificar arquivos.
    """

    source = source.expanduser().resolve()
    storage_path = storage_path.expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(
            f"ISO não encontrada: {source}"
        )

    if not source.is_file():
        raise IsADirectoryError(
            f"O caminho não é um arquivo: {source}"
        )

    file_size = source.stat().st_size

    part_count = calculate_ul_parts(
        file_size
    )

    ul_title = normalize_ul_title(title)
    crc = ul_crc32(ul_title)

    part_paths = tuple(
        storage_path
        / build_ul_part_name(
            ul_title,
            game_id,
            part,
        )
        for part in range(part_count)
    )

    return ULInstallPlan(
        source=source,
        storage_path=storage_path,
        title=ul_title,
        game_id=game_id,
        media_type=media_type,
        file_size=file_size,
        part_size=UL_PART_SIZE,
        part_count=part_count,
        crc32=crc,
        part_paths=part_paths,
        cfg_path=storage_path / "ul.cfg",
    )
    
def build_ul_record(
    title: str,
    game_id: str,
    parts: int,
    media_type: MediaType,
) -> bytes:
    """
    Gera um registro de 64 bytes compatível com ul.cfg.
    """

    if not title:
        raise ValueError(
            "O título UL não pode ser vazio."
        )

    try:
        title_bytes = title.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(
            "O título UL deve conter apenas caracteres ASCII."
        ) from exc

    if len(title_bytes) > 32:
        raise ValueError(
            "O título UL não pode exceder 32 bytes."
        )

    try:
        game_id_bytes = game_id.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(
            "Game ID inválido."
        ) from exc

    if len(game_id_bytes) > 12:
        raise ValueError(
            "Game ID não pode exceder 12 bytes."
        )

    if not 1 <= parts <= 255:
        raise ValueError(
            "Quantidade de partes UL inválida."
        )

    if media_type == MediaType.CD:
        media = UL_MEDIA_CD

    elif media_type == MediaType.DVD:
        media = UL_MEDIA_DVD

    else:
        raise ValueError(
            f"Tipo de mídia UL não suportado: {media_type}"
        )

    record = bytearray(UL_RECORD_SIZE)

    # 0x00 - 0x1F
    # Nome do jogo: 32 bytes.
    record[0:len(title_bytes)] = title_bytes

    # 0x20 - 0x22
    record[0x20:0x23] = b"ul."

    # 0x23 - 0x2E
    # Startup / Game ID.
    record[0x23:0x23 + len(game_id_bytes)] = game_id_bytes

    # 0x2F
    record[0x2F] = parts

    # 0x30
    record[0x30] = media

    # 0x31 - 0x34 permanecem zero.

    # 0x35
    record[0x35] = 0x08

    # 0x36 - 0x3F permanecem zero.

    return bytes(record)

def parse_ul_record(
    record: bytes,
) -> ULGame:
    """
    Interpreta um registro de 64 bytes do ul.cfg.
    """

    if len(record) != UL_RECORD_SIZE:
        raise ValueError(
            f"Registro UL deve possuir exatamente "
            f"{UL_RECORD_SIZE} bytes."
        )

    title = (
        record[0x00:0x20]
        .split(b"\x00", 1)[0]
        .decode("ascii", errors="replace")
    )

    magic = record[0x20:0x23]

    if magic != b"ul.":
        raise ValueError(
            f"Magic UL inválido: {magic!r}"
        )

    game_id = (
        record[0x23:0x2F]
        .split(b"\x00", 1)[0]
        .decode("ascii", errors="replace")
    )

    parts = record[0x2F]
    media = record[0x30]

    if media == UL_MEDIA_CD:
        media_type = MediaType.CD

    elif media == UL_MEDIA_DVD:
        media_type = MediaType.DVD

    else:
        raise ValueError(
            f"Tipo de mídia UL desconhecido: "
            f"0x{media:02X}"
        )

    return ULGame(
        title=title,
        game_id=game_id,
        parts=parts,
        media_type=media_type,
    )
    
def read_ul_cfg(
    path: str | Path,
) -> list[ULGame]:
    """
    Lê e interpreta todas as entradas de um ul.cfg.
    """

    records = read_ul_records(path)

    return [
        parse_ul_record(record)
        for record in records
    ]
    
def normalize_ul_title(
    title: str,
) -> str:
    """
    Normaliza um título para os limites do formato UL.
    """

    try:
        encoded = title.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(
            "O título UL contém caracteres não ASCII."
        ) from exc

    if len(encoded) <= UL_TITLE_MAX_BYTES:
        return title

    encoded = encoded[:UL_TITLE_MAX_BYTES]

    return encoded.decode("ascii").rstrip()

def write_ul_parts(
    plan: ULInstallPlan,
    *,
    progress_callback=None,
    chunk_size: int = 4 * 1024 * 1024,
) -> tuple[Path, ...]:
    """
    Divide a ISO nas partes UL.

    Não modifica ul.cfg.
    Não sobrescreve partes existentes.
    """

    created_files: list[Path] = []
    total_written = 0

    # Segurança antes de começar.
    existing = [
        path
        for path in plan.part_paths
        if path.exists()
    ]

    if existing:
        raise ULInstallError(
            "Já existem partes UL para este jogo: "
            + ", ".join(str(path) for path in existing)
        )

    try:
        with plan.source.open("rb") as source:
            for part_path in plan.part_paths:
                part_written = 0

                with part_path.open("xb") as destination:
                    created_files.append(part_path)

                    while part_written < plan.part_size:
                        remaining = (
                            plan.part_size - part_written
                        )

                        data = source.read(
                            min(chunk_size, remaining)
                        )

                        if not data:
                            break

                        destination.write(data)

                        part_written += len(data)
                        total_written += len(data)

                        if progress_callback is not None:
                            progress_callback(total_written)

                    destination.flush()
                    os.fsync(destination.fileno())

        if total_written != plan.file_size:
            raise ULInstallError(
                "Quantidade de dados gravados não corresponde "
                "ao tamanho da ISO. "
                f"ISO={plan.file_size}; "
                f"gravado={total_written}."
            )

    except (Exception, KeyboardInterrupt):
        for path in created_files:
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass

        raise

    return tuple(created_files)

def calculate_file_sha256(
    path: Path,
    *,
    progress_callback=None,
    chunk_size: int = 4 * 1024 * 1024,
) -> str:
    digest = hashlib.sha256()
    processed = 0

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)

            processed += len(chunk)

            if progress_callback is not None:
                progress_callback(processed)

    return digest.hexdigest()

def calculate_ul_parts_sha256(
    part_paths: tuple[Path, ...],
    *,
    progress_callback=None,
    chunk_size: int = 4 * 1024 * 1024,
) -> str:
    """
    Calcula SHA-256 tratando as partes UL como
    um único fluxo contínuo.
    """

    digest = hashlib.sha256()
    processed = 0

    for part_path in part_paths:
        with part_path.open("rb") as file:
            while chunk := file.read(chunk_size):
                digest.update(chunk)

                processed += len(chunk)

                if progress_callback is not None:
                    progress_callback(processed)

    return digest.hexdigest()

def verify_ul_parts(
    plan: ULInstallPlan,
    part_paths: tuple[Path, ...],
    *,
    source_progress_callback=None,
    parts_progress_callback=None,
) -> None:
    source_hash = calculate_file_sha256(
        plan.source,
        progress_callback=source_progress_callback,
    )

    parts_hash = calculate_ul_parts_sha256(
        part_paths,
        progress_callback=parts_progress_callback,
    )

    if source_hash != parts_hash:
        raise ULInstallError(
            "Falha na verificação SHA-256 das partes UL."
        )

def install_ul_parts(
    plan: ULInstallPlan,
    *,
    free_space: int,
    copy_progress_callback=None,
    source_hash_progress_callback=None,
    parts_hash_progress_callback=None,
) -> tuple[Path, ...]:
    """
    Instala e valida as partes de um jogo UL.

    Nesta etapa, ul.cfg NÃO é modificado.
    """

    if free_space < plan.file_size:
        raise ULInstallError(
            "Espaço insuficiente no dispositivo. "
            f"Necessário: {plan.file_size} bytes; "
            f"disponível: {free_space} bytes."
        )

    existing = [
        path
        for path in plan.part_paths
        if path.exists()
    ]

    if existing:
        raise ULInstallError(
            "Já existem partes UL para este jogo: "
            + ", ".join(str(path) for path in existing)
        )

    part_paths: tuple[Path, ...] = ()

    try:
        part_paths = write_ul_parts(
            plan,
            progress_callback=copy_progress_callback,
        )

        verify_ul_parts(
            plan,
            part_paths,
            source_progress_callback=(
                source_hash_progress_callback
            ),
            parts_progress_callback=(
                parts_hash_progress_callback
            ),
        )

    except (Exception, KeyboardInterrupt):
        for path in part_paths:
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass

        raise

    return part_paths

def register_ul_game(
    plan: ULInstallPlan,
) -> Path:
    """
    Registra no ul.cfg um jogo cujas partes UL já existem.

    As partes não são modificadas.
    """

    # Todas as partes precisam existir.
    missing_parts = [
        path
        for path in plan.part_paths
        if not path.is_file()
    ]

    if missing_parts:
        raise ULInstallError(
            "Não é possível registrar o jogo. "
            "Partes UL ausentes: "
            + ", ".join(str(path) for path in missing_parts)
        )

    # Confere o tamanho das partes.
    total_size = 0

    for index, part_path in enumerate(plan.part_paths):
        size = part_path.stat().st_size
        total_size += size

        is_last = index == len(plan.part_paths) - 1

        if not is_last and size != plan.part_size:
            raise ULInstallError(
                f"Tamanho inválido da parte {part_path.name}: "
                f"esperado={plan.part_size}; encontrado={size}."
            )

        if is_last:
            expected_last_size = (
                plan.file_size
                - plan.part_size * (plan.part_count - 1)
            )

            if size != expected_last_size:
                raise ULInstallError(
                    f"Tamanho inválido da última parte "
                    f"{part_path.name}: "
                    f"esperado={expected_last_size}; "
                    f"encontrado={size}."
                )

    if total_size != plan.file_size:
        raise ULInstallError(
            "O tamanho total das partes UL não corresponde "
            "ao tamanho da ISO."
        )

    record = build_ul_record(
        title=plan.title,
        game_id=plan.game_id,
        parts=plan.part_count,
        media_type=plan.media_type,
    )

    if len(record) != UL_RECORD_SIZE:
        raise ULInstallError(
            "Registro UL gerado com tamanho inválido."
        )

    cfg_path = plan.cfg_path

    existing_data = b""

    if cfg_path.exists():
        existing_data = cfg_path.read_bytes()

        if len(existing_data) % UL_RECORD_SIZE != 0:
            raise ULInstallError(
                f"ul.cfg inválido: tamanho "
                f"{len(existing_data)} não é múltiplo de "
                f"{UL_RECORD_SIZE}."
            )

        existing_records = [
            existing_data[offset:offset + UL_RECORD_SIZE]
            for offset in range(
                0,
                len(existing_data),
                UL_RECORD_SIZE,
            )
        ]

        for existing_record in existing_records:
            game = parse_ul_record(existing_record)

            if game.game_id == plan.game_id:
                raise ULInstallError(
                    f"O jogo {plan.game_id} já está "
                    "registrado no ul.cfg."
                )

    new_data = existing_data + record

    temp_path = cfg_path.with_name(
        f"{cfg_path.name}.tmp"
    )

    if temp_path.exists():
        raise ULInstallError(
            f"Arquivo temporário já existe: {temp_path}"
        )

    try:
        with temp_path.open("xb") as file:
            file.write(new_data)
            file.flush()
            os.fsync(file.fileno())

        # Validação do arquivo temporário antes de
        # substituir/criar ul.cfg.
        temp_data = temp_path.read_bytes()

        if temp_data != new_data:
            raise ULInstallError(
                "Falha ao validar o ul.cfg temporário."
            )

        if len(temp_data) % UL_RECORD_SIZE != 0:
            raise ULInstallError(
                "ul.cfg temporário possui tamanho inválido."
            )

        # Valida todos os registros usando nosso parser.
        for offset in range(
            0,
            len(temp_data),
            UL_RECORD_SIZE,
        ):
            parse_ul_record(
                temp_data[
                    offset:offset + UL_RECORD_SIZE
                ]
            )

        os.replace(
            temp_path,
            cfg_path,
        )

    except (Exception, KeyboardInterrupt):
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

        raise

    # Reabre o arquivo definitivo.
    final_data = cfg_path.read_bytes()

    if final_data != new_data:
        raise ULInstallError(
            "Falha na verificação final do ul.cfg."
        )

    return cfg_path