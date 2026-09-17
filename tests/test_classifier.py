from pathlib import Path

import pytest

from smart_organizer.classifier import classify


@pytest.mark.parametrize(
    ("filename", "category"),
    [
        ("photo.JPG", "Images"),
        ("letter.docx", "Documents"),
        ("budget.csv", "Spreadsheets"),
        ("invoice.pdf", "PDFs"),
        ("song.mp3", "Audio"),
        ("clip.mp4", "Video"),
        ("backup.zip", "Archives"),
        ("script.py", "Code"),
        ("mystery.xyz", "Other"),
        ("no_extension", "Other"),
    ],
)
def test_classify(filename: str, category: str) -> None:
    assert classify(Path(filename)) == category
