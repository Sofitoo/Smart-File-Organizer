"""Plan and perform moves for files directly inside a folder."""

import logging
import os
from pathlib import Path
import shutil
from time import perf_counter

from .classifier import classify
from .reporter import Move, Report

LOGGER = logging.getLogger(__name__)


def available_destination(folder: Path, name: str, reserved: set[Path]) -> Path:
    """Choose a free filename, including names planned earlier in this run."""
    original = Path(name)
    candidate = folder / name
    number = 1
    while candidate.exists() or candidate.is_symlink() or candidate in reserved:
        candidate = folder / f"{original.stem}_{number}{original.suffix}"
        number += 1
    return candidate


def move_without_overwrite(source: Path, destination: Path) -> None:
    """Reserve a destination exclusively before moving into it."""
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    os.close(descriptor)
    try:
        shutil.move(str(source), str(destination))
    except OSError:
        destination.unlink(missing_ok=True)
        raise


def organize(
    folder: Path, *, dry_run: bool = False, report_path: Path | None = None, quiet: bool = False
) -> Report:
    """Organize immediate, visible regular files; never recurse into folders."""
    started = perf_counter()
    folder = folder.expanduser().resolve()
    if not folder.is_dir():
        raise ValueError(f"Not a directory: {folder}")

    report = Report(source=folder, dry_run=dry_run)
    reserved: set[Path] = set()
    excluded_report = report_path.expanduser().absolute() if report_path else None

    for entry in sorted(folder.iterdir(), key=lambda path: path.name):
        if (
            entry.name.startswith(".")
            or entry.is_symlink()
            or not entry.is_file()
            or entry == excluded_report
        ):
            report.ignored.append(entry.name)
            continue

        report.processed += 1
        category = classify(entry)
        destination_folder = folder / category
        if destination_folder.is_symlink() or (
            destination_folder.exists() and not destination_folder.is_dir()
        ):
            message = f"Category path is not a regular directory: {destination_folder}"
            report.errors.append({"file": entry.name, "error": message})
            report.moves.append(Move(entry.name, category, f"{category}/{entry.name}", "error"))
            LOGGER.error(message)
            continue
        destination = available_destination(destination_folder, entry.name, reserved)
        reserved.add(destination)
        LOGGER.info("%s -> %s", entry, destination)

        if dry_run:
            report.moves.append(Move(entry.name, category, f"{category}/{destination.name}", "ready"))
            if not quiet:
                print(f"{entry.name} -> {category}/{destination.name}")
            report.moved_by_category[category] += 1
            continue

        try:
            destination_folder.mkdir(exist_ok=True)
            move_without_overwrite(entry, destination)
        except FileExistsError:
            # Another process claimed the planned name. Find and reserve a new one.
            try:
                destination = available_destination(destination_folder, entry.name, reserved)
                reserved.add(destination)
                move_without_overwrite(entry, destination)
            except OSError as error:
                report.errors.append({"file": entry.name, "error": str(error)})
                report.moves.append(Move(entry.name, category, f"{category}/{destination.name}", "error"))
                LOGGER.error("Could not move %s: %s", entry, error)
                continue
        except OSError as error:
            report.errors.append({"file": entry.name, "error": str(error)})
            report.moves.append(Move(entry.name, category, f"{category}/{destination.name}", "error"))
            LOGGER.error("Could not move %s: %s", entry, error)
            continue

        report.moved_by_category[category] += 1
        report.moves.append(Move(entry.name, category, f"{category}/{destination.name}", "moved"))
        if not quiet:
            print(f"{entry.name} -> {category}/{destination.name}")

    report.elapsed_seconds = perf_counter() - started
    return report
