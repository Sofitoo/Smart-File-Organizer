"""Classify a file from its extension."""

from pathlib import Path

from .config import EXTENSIONS


def classify(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, extensions in EXTENSIONS.items():
        if suffix in extensions:
            return category
    return "Other"
