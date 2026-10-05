import re
from dataclasses import dataclass

GAME_ID_PATTERN = re.compile(
    r"([A-Z]{4})[_-](\d{3})[._](\d{2})",
    re.IGNORECASE,
)

@dataclass(frozen=True)
class SystemConfig:
    game_id: str | None = None
    version: str | None = None
    video_mode: str | None = None


def parse_system_cnf(content: str) -> SystemConfig:
    """
    Interpreta o conteúdo de um SYSTEM.CNF de PlayStation 2.
    """

    values: dict[str, str] = {}

    for line in content.splitlines():
        line = line.strip()

        if not line or "=" not in line:
            continue

        key, value = line.split("=", maxsplit=1)

        values[key.strip().upper()] = value.strip()

    boot = values.get("BOOT2", "")

    game_id = None

    match = GAME_ID_PATTERN.search(boot)

    if match:
        prefix, number, suffix = match.groups()

        game_id = (
            f"{prefix.upper()}_"
            f"{number}."
            f"{suffix}"
        )

    return SystemConfig(
        game_id=game_id,
        version=values.get("VER"),
        video_mode=values.get("VMODE"),
    )