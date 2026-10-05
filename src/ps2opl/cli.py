import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from ps2opl import __version__
from ps2opl.iso import find_iso_files, read_system_cnf
from ps2opl.logging_config import configure_logging
from ps2opl.system_cnf import parse_system_cnf

app = typer.Typer(
    name="ps2opl",
    help="Utilitário CLI para gerenciamento de jogos do Open PS2 Loader.",
    no_args_is_help=True,
)

console = Console()

logger = logging.getLogger("ps2opl")

def format_size(size: int) -> str:
    """
    Converte um tamanho em bytes para uma representação legível.
    """

    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{size} B"


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging.",
    ),
) -> None:
    configure_logging(verbose)

@app.command()
def version() -> None:
    """Show ps2opl version."""
    typer.echo(f"ps2opl {__version__}")

@app.command()
def scan(
    path: Annotated[
        Path,
        typer.Argument(
            help="Diretório onde as ISOs serão procuradas.",
        ),
    ],
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive/--no-recursive",
            "-r/-R",
            help="Procura ISOs também nos subdiretórios.",
        ),
    ] = True,
) -> None:
    """
    Localiza imagens ISO de PlayStation 2.
    """

    logger.info("Procurando ISOs em: %s", path)

    try:
        iso_files = find_iso_files(
            path,
            recursive=recursive,
        )

    except (FileNotFoundError, NotADirectoryError) as exc:
        logger.error("%s", exc)
        raise typer.Exit(code=1) from exc

    if not iso_files:
        console.print()
        console.print("[yellow]Nenhuma ISO encontrada.[/yellow]")
        return

    table = Table(
        title="ISOs encontradas",
        show_header=True,
        header_style="bold",
    )

    table.add_column("#", justify="right")
    table.add_column("Game ID")
    table.add_column("Arquivo")
    table.add_column("Versão")
    table.add_column("Vídeo")
    table.add_column("Tamanho", justify="right")
    table.add_column("Caminho")

    total_size = 0
    valid_games = 0
    errors = 0

    for index, iso_file in enumerate(iso_files, start=1):
        size = iso_file.stat().st_size
        total_size += size

        game_id = "-"
        version = "-"
        video_mode = "-"

        try:
            system_cnf = read_system_cnf(iso_file)
            config = parse_system_cnf(system_cnf)

            game_id = config.game_id or "-"
            version = config.version or "-"
            video_mode = config.video_mode or "-"

            if config.game_id:
                valid_games += 1

            logger.debug(
                "ISO analisada: path=%s game_id=%s version=%s video_mode=%s",
                iso_file,
                game_id,
                version,
                video_mode,
            )

        except (ValueError, OSError) as exc:
            errors += 1

            logger.warning(
                "Não foi possível analisar '%s': %s",
                iso_file.name,
                exc,
            )

        table.add_row(
            str(index),
            game_id,
            iso_file.name,
            version,
            video_mode,
            format_size(size),
            str(iso_file.parent),
        )

    console.print()
    console.print(table)
    console.print()

    console.print(
        f"[bold]{len(iso_files)}[/bold] ISO(s) encontrada(s) "
        f"— [green]{valid_games}[/green] jogo(s) identificado(s) "
        f"— tamanho total: [bold]{format_size(total_size)}[/bold]"
    )

    if errors:
        console.print(
            f"[yellow]{errors} ISO(s) não puderam ser analisadas.[/yellow]"
        )
