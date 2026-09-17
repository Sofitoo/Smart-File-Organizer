import json
from pathlib import Path

import pytest

from smart_organizer.cli import main
from smart_organizer.organizer import organize


def test_dry_run_does_not_change_files(tmp_path: Path, capsys) -> None:
    (tmp_path / "photo.png").write_text("picture")
    (tmp_path / "Images").mkdir()
    (tmp_path / "Images" / "photo.png").write_text("existing")

    report = organize(tmp_path, dry_run=True)

    assert (tmp_path / "photo.png").read_text() == "picture"
    assert (tmp_path / "Images" / "photo.png").read_text() == "existing"
    assert not (tmp_path / "Images" / "photo_1.png").exists()
    assert "photo.png -> Images/photo_1.png" in capsys.readouterr().out
    assert report.moved_by_category["Images"] == 1


def test_duplicate_gets_safe_name(tmp_path: Path) -> None:
    (tmp_path / "document.pdf").write_text("new")
    (tmp_path / "PDFs").mkdir()
    (tmp_path / "PDFs" / "document.pdf").write_text("old")
    (tmp_path / "PDFs" / "document_1.pdf").write_text("also old")

    report = organize(tmp_path)

    assert (tmp_path / "PDFs" / "document.pdf").read_text() == "old"
    assert (tmp_path / "PDFs" / "document_1.pdf").read_text() == "also old"
    assert (tmp_path / "PDFs" / "document_2.pdf").read_text() == "new"
    assert report.moved_by_category["PDFs"] == 1


def test_organizes_and_ignores_existing_folders_and_hidden_files(tmp_path: Path) -> None:
    (tmp_path / "photo.JPG").write_text("image")
    (tmp_path / "data.csv").write_text("spreadsheet")
    (tmp_path / "unknown.xyz").write_text("unknown")
    (tmp_path / ".secret.pdf").write_text("hidden")
    (tmp_path / "Documents").mkdir()
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "nested.pdf").write_text("nested")

    report = organize(tmp_path)

    assert (tmp_path / "Images" / "photo.JPG").read_text() == "image"
    assert (tmp_path / "Spreadsheets" / "data.csv").read_text() == "spreadsheet"
    assert (tmp_path / "Other" / "unknown.xyz").read_text() == "unknown"
    assert (tmp_path / ".secret.pdf").exists()
    assert (tmp_path / "nested" / "nested.pdf").exists()
    assert report.processed == 3
    assert set(report.ignored) == {".secret.pdf", "Documents", "nested"}
    assert report.errors == []
    assert report.elapsed_seconds >= 0


def test_cli_writes_json_report_and_ignores_it_next_time(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("hello")
    report_path = tmp_path / "report.json"

    assert main(["organize", str(tmp_path), "--report", str(report_path)]) == 0
    data = json.loads(report_path.read_text())
    assert data["processed"] == 1
    assert data["moved_by_category"]["Documents"] == 1
    assert data["ignored"] == []
    assert data["errors"] == []

    assert main(["organize", str(tmp_path), "--report", str(report_path)]) == 0
    assert json.loads(report_path.read_text())["ignored"] == ["Documents", "report.json"]


def test_category_name_is_not_ignored_if_it_is_a_file(tmp_path: Path) -> None:
    (tmp_path / "Images").write_text("plain file")

    report = organize(tmp_path)

    assert (tmp_path / "Other" / "Images").read_text() == "plain file"
    assert report.processed == 1


def test_cli_rejects_report_in_dry_run(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"

    with pytest.raises(SystemExit) as error:
        main(["organize", str(tmp_path), "--dry-run", "--report", str(report_path)])

    assert error.value.code == 2
    assert not report_path.exists()


def test_category_symlink_is_not_used_as_destination(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "Images").symlink_to(outside, target_is_directory=True)
    (tmp_path / "photo.png").write_text("picture")

    report = organize(tmp_path)

    assert (tmp_path / "photo.png").exists()
    assert not (outside / "photo.png").exists()
    assert len(report.errors) == 1
