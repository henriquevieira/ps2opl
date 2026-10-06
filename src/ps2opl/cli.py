import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from ps2opl import __version__
from ps2opl.install import (
    InstallError,
    InstallMethod,
    create_install_plan,
    install_iso,
)
from ps2opl.iso import (
    detect_media_type,
    find_iso_files,
    read_system_cnf,
)
from ps2opl.logging_config import configure_logging
from ps2opl.storage import inspect_opl_storage
from ps2opl.system_cnf import parse_system_cnf

app = typer.Typer(
    name="ps2opl",
    help="CLI utility for managing Open PS2 Loader games.",
    no_args_is_help=True,
)

console = Console()

logger = logging.getLogger("ps2opl")

def format_size(size: int) -> str:
    """
    Converts a size in bytes to a human-readable representation..
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
            help="Directory where ISOs will be searched for.",
        ),
    ],
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive/--no-recursive",
            "-r/-R",
            help="Also searches for ISOs in subdirectories.",
        ),
    ] = True,
) -> None:
    """
    Locates PlayStation 2 ISO images.
    """

    logger.info("Looking for ISOs in: %s", path)

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
        console.print("[yellow]No ISO found.[/yellow]")
        return

    table = Table(
        title="ISOs found",
        show_header=True,
        header_style="bold",
    )

    table.add_column("#", justify="right")
    table.add_column("Game ID")
    table.add_column("File")
    table.add_column("Media type")
    table.add_column("Version")
    table.add_column("Video")
    table.add_column("Size", justify="right")
    table.add_column("Path")

    total_size = 0
    valid_games = 0
    errors = 0

    for index, iso_file in enumerate(iso_files, start=1):
        size = iso_file.stat().st_size
        total_size += size

        game_id = "-"
        media_type = "-"
        version = "-"
        video_mode = "-"
        
        try:
            media_type = detect_media_type(iso_file).value

            system_cnf = read_system_cnf(iso_file)
            config = parse_system_cnf(system_cnf)

            game_id = config.game_id or "-"
            version = config.version or "-"
            video_mode = config.video_mode or "-"

            if config.game_id:
                valid_games += 1

        except (ValueError, OSError) as exc:
            errors += 1

            logger.warning(
                "Unable to analyze '%s': %s",
                iso_file.name,
                exc,
            )

        try:
            system_cnf = read_system_cnf(iso_file)
            config = parse_system_cnf(system_cnf)

            game_id = config.game_id or "-"
            version = config.version or "-"
            video_mode = config.video_mode or "-"

            if config.game_id:
                valid_games += 1

            logger.debug(
                "ISO analyzed: path=%s game_id=%s version=%s video_mode=%s",
                iso_file,
                game_id,
                version,
                video_mode,
            )

        except (ValueError, OSError) as exc:
            errors += 1

            logger.warning(
                "Unable to analyze '%s': %s",
                iso_file.name,
                exc,
            )

        table.add_row(
            str(index),
            game_id,
            iso_file.name,
            media_type,
            version,
            video_mode,
            format_size(size),
            str(iso_file.parent),
        )

    console.print()
    console.print(table)
    console.print()

    console.print(
        f"[bold]{len(iso_files)}[/bold] ISO(s) found "
        f"— [green]{valid_games}[/green] game(s) identified "
        f"— total size: [bold]{format_size(total_size)}[/bold]"
    )

    if errors:
        console.print(
            f"[yellow]{errors} The ISO(s) could not be analyzed.[/yellow]"
        )

@app.command()
def device(
    path: Annotated[
        Path,
        typer.Argument(
            help="OPL device mount point.",
        ),
    ],
) -> None:
    """
    Detects and validates an OPL storage device.
    """

    logger.info(
        "Inspecting device: %s",
        path,
    )

    try:
        storage = inspect_opl_storage(path)

    except (FileNotFoundError, NotADirectoryError) as exc:
        logger.error("%s", exc)
        raise typer.Exit(code=1) from exc

    console.print()
    console.print("[bold]Open PS2 Loader Storage[/bold]")
    console.print()

    console.print(
        f"[bold]Path:[/bold]        {storage.path}"
    )

    console.print(
        f"[bold]Filesystem:[/bold]  "
        f"{storage.filesystem or 'desconhecido'}"
    )

    console.print(
        f"[bold]Total:[/bold]       "
        f"{format_size(storage.total_space)}"
    )

    console.print(
        f"[bold]Used:[/bold]       "
        f"{format_size(storage.used_space)}"
    )

    console.print(
        f"[bold]Free:[/bold]       "
        f"{format_size(storage.free_space)}"
    )

    console.print()
    console.print("[bold]OPL Structure[/bold]")
    console.print()

    for directory, exists in storage.required_directories.items():
        status = "[green]✓[/green]" if exists else "[red]✗[/red]"

        console.print(
            f"{status} {directory}/ [bold](mandatory)[/bold]"
        )

    for directory, exists in storage.optional_directories.items():
        status = "[green]✓[/green]" if exists else "[dim]−[/dim]"

        console.print(
            f"{status} {directory}/"
        )

    console.print()

    if storage.is_valid:
        console.print(
            "[green bold]✓ Valid OPL structure.[/green bold]"
        )
    else:
        console.print(
            "[red bold]✗ Incomplete OPL structure.[/red bold]"
        )

    if storage.is_fat32:
        console.print(
            "[yellow]FAT32 filesystem detected: "
            "individual files are subject to the 4 GiB "
            "limit.[/yellow]"
        )
        
@app.command()
def install(
    iso: Annotated[
        Path,
        typer.Argument(
            help="ISO image to be installed.",
        ),
    ],
    device: Annotated[
        Path,
        typer.Argument(
            help="OPL device mount point.",
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Displays the plan without modifying the device.",
        ),
    ] = False,
) -> None:
    """
    Installs a game on an OPL device.
    """

    logger.info(
        "Preparing installation: %s",
        iso,
    )

    try:
        storage = inspect_opl_storage(device)

        if not storage.is_valid:
            console.print(
                "[red]The destination does not have a valid "
                "OPL structure.[/red]"
            )
            raise typer.Exit(code=1)

        plan = create_install_plan(
            iso,
            storage,
        )

    except (
        FileNotFoundError,
        IsADirectoryError,
        ValueError,
    ) as exc:
        logger.error("%s", exc)
        raise typer.Exit(code=1) from exc

    console.print()
    console.print("[bold]Installation plan[/bold]")
    console.print()

    console.print(
        f"[bold]Origin:[/bold]       {plan.source}"
    )

    console.print(
        f"[bold]Game ID:[/bold]      {plan.game_id}"
    )

    console.print(
        f"[bold]Media Type:[/bold]        {plan.media_type.value}"
    )

    console.print(
        f"[bold]Size:[/bold]      {format_size(plan.file_size)}"
    )

    console.print(
        f"[bold]Filesystem:[/bold]   "
        f"{storage.filesystem or 'desconhecido'}"
    )

    console.print(
        f"[bold]Method:[/bold]       {plan.method.value}"
    )

    if plan.destination is not None:
        console.print(
            f"[bold]Destination:[/bold]      {plan.destination}"
        )

    if plan.requires_ul:
        console.print()
        console.print(
            "[yellow]The ISO exceeds the FAT32 file size limit.[/yellow]"
        )
        console.print(
            "[yellow]Installation in UL/USBExtreme format will be required.[/yellow]"
        )

    console.print()

    if dry_run:
        console.print(
            "[cyan bold]DRY RUN — No files were modified.[/cyan bold]"
        )
        return

    if plan.method == InstallMethod.UL:
        console.print(
            "[yellow]The UL/USBExtreme installation is not yet "
            "implemented.[/yellow]"
        )
        raise typer.Exit(code=2)
    
        console.print()

    confirmed = typer.confirm(
        "Do you want to start the installation?"
    )

    if not confirmed:
        console.print(
            "[yellow]Canceled installation.[/yellow]"
        )
        raise typer.Exit()
    
    console.print()

    try:
        with Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:

            copy_task = progress.add_task(
                "[blue]Copying files to pendrive, please wait...",
                total=plan.file_size,
            )

            source_hash_task = progress.add_task(
                "[cyan]Checking origin",
                total=plan.file_size,
                visible=False,
            )

            destination_hash_task = progress.add_task(
                "[cyan]Checking destination",
                total=plan.file_size,
                visible=False,
            )

            def update_copy(processed: int) -> None:
                progress.update(
                    copy_task,
                    completed=processed,
                )

            def update_source_hash(processed: int) -> None:
                progress.update(
                    source_hash_task,
                    visible=True,
                    completed=processed,
                )

                progress.update(
                    source_hash_task,
                    visible=True,
                    completed=processed,
                )

            def update_destination_hash(processed: int) -> None:
                progress.update(
                    destination_hash_task,
                    visible=True,
                    completed=processed,
                )

                progress.update(
                    destination_hash_task,
                    visible=True,
                    completed=processed,
                )

            destination = install_iso(
                plan,
                storage,
                copy_progress_callback=update_copy,
                source_hash_progress_callback=update_source_hash,
                destination_hash_progress_callback=update_destination_hash,
            )

            progress.update(
                destination_hash_task,
                completed=plan.file_size,
            )

    except InstallError as exc:
        console.print()
        console.print(
            f"[red bold]Installation failed:[/red bold] {exc}"
        )

        raise typer.Exit(code=1) from exc

    except OSError as exc:
        console.print()
        console.print(
            f"[red bold]I/O error:[/red bold] {exc}"
        )

        raise typer.Exit(code=1) from exc

    console.print()
    console.print(
        "[green bold]✓ Installation completed successfully.[/green bold]"
    )

    console.print(
        f"[bold]Destination:[/bold] {destination}"
    )