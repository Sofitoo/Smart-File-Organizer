import asyncio
from pathlib import Path

import httpx

from smart_organizer.web import routes


def request(method: str, url: str, **kwargs: object) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=routes.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, url, **kwargs)

    return asyncio.run(send())


def test_web_page_and_health() -> None:
    assert request("GET", "/health").json() == {"status": "ok"}
    page = request("GET", "/")
    assert page.status_code == 200
    assert "Smart File Organizer" in page.text
    assert "Organization Preview" in page.text
    assert request("GET", "/static/styles.css").status_code == 200
    assert request("GET", "/static/app.js").status_code == 200


def test_preview_uses_real_plan_without_writing(tmp_path: Path) -> None:
    (tmp_path / "photo.jpg").write_text("photo")
    (tmp_path / "PDFs").mkdir()
    (tmp_path / "PDFs" / "report.pdf").write_text("old")
    (tmp_path / "report.pdf").write_text("new")
    (tmp_path / ".secret.txt").write_text("hidden")

    response = request("POST", "/api/preview", json={"path": str(tmp_path)})

    assert response.status_code == 200
    report = response.json()
    assert report["dry_run"] is True
    assert report["processed"] == 2
    assert {move["destination"] for move in report["moves"]} == {
        "Images/photo.jpg", "PDFs/report_1.pdf"
    }
    assert report["ignored"] == [".secret.txt", "PDFs"]
    assert (tmp_path / "photo.jpg").exists()
    assert (tmp_path / "report.pdf").exists()
    assert not (tmp_path / "Images").exists()


def test_execution_moves_files_and_keeps_existing_destination(tmp_path: Path) -> None:
    (tmp_path / "report.pdf").write_text("new")
    (tmp_path / "PDFs").mkdir()
    (tmp_path / "PDFs" / "report.pdf").write_text("old")

    response = request("POST", "/api/organize", json={"path": str(tmp_path)})

    assert response.status_code == 200
    report = response.json()
    assert report["dry_run"] is False
    assert report["moves"][0]["status"] == "moved"
    assert report["moves"][0]["destination"] == "PDFs/report_1.pdf"
    assert (tmp_path / "PDFs" / "report.pdf").read_text() == "old"
    assert (tmp_path / "PDFs" / "report_1.pdf").read_text() == "new"


def test_invalid_paths_are_rejected(tmp_path: Path) -> None:
    for path in ["relative", str(tmp_path / ".." / tmp_path.name), str(tmp_path / "missing"), "/"]:
        assert request("POST", "/api/preview", json={"path": path}).status_code == 400
    link = tmp_path / "link"
    link.symlink_to(tmp_path, target_is_directory=True)
    assert request("POST", "/api/preview", json={"path": str(link)}).status_code == 400


def test_organizer_error_is_returned_as_server_error(tmp_path: Path, monkeypatch) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("test failure")

    monkeypatch.setattr(routes, "organize", fail)
    response = request("POST", "/api/preview", json={"path": str(tmp_path)})

    assert response.status_code == 500
    assert response.json()["detail"] == "Could not analyze the folder."


def test_organizer_file_error_is_reported_without_moving_outside(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "Images").symlink_to(outside, target_is_directory=True)
    (tmp_path / "photo.jpg").write_text("photo")

    response = request("POST", "/api/organize", json={"path": str(tmp_path)})

    assert response.status_code == 200
    assert response.json()["processed"] == 1
    assert len(response.json()["errors"]) == 1
    assert response.json()["moves"][0]["status"] == "error"
    assert (tmp_path / "photo.jpg").exists()
    assert not (outside / "photo.jpg").exists()
