import re
from pathlib import Path

REGION_SUFFIX_PATTERN = re.compile(
    r"\s+\("
    r"(USA|Europe|Japan|World|Brazil|Australia)"
    r"(?:,[^)]+)?"
    r"\)$",
    re.IGNORECASE,
)

OPL_PREFIX_PATTERN = re.compile(
    r"^[A-Z]{4}[_-]\d{3}[._]\d{2}\.",
    re.IGNORECASE,
)


def get_game_title(iso_path: str | Path) -> str:
    """
    Extracts the game title from the ISO filename. 

    Removes the following, if present:
    - OPL Game ID prefix; 
    - region information at the end. 

    Examples:

        Ben 10 - Protector of Earth (USA).iso
        SLUS_216.61.Ben 10 - Protector of Earth.iso

    become:

        Ben 10 - Protector of Earth
    """

    path = Path(iso_path)

    title = path.stem.strip()

    title = OPL_PREFIX_PATTERN.sub("", title)

    title = REGION_SUFFIX_PATTERN.sub("", title)

    return title.strip()


def sanitize_opl_title(title: str) -> str:
    """
    Removes characters unsuitable for filenames. 

    Keeps the title readable and storage-compatible.
    """

    invalid_characters = '<>:"/\\|?*'

    for character in invalid_characters:
        title = title.replace(character, "-")

    title = re.sub(r"\s+", " ", title)

    return title.strip(" .")


def build_opl_filename(
    iso_path: str | Path,
    game_id: str,
) -> str:
    """
    Generates the ISO name expected by OPL. 

    Example:

        SLUS_216.61.Ben 10 - Protector of Earth.iso
    """

    title = get_game_title(iso_path)

    title = sanitize_opl_title(title)

    return f"{game_id}.{title}.iso"