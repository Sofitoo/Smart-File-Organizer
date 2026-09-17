"""Structured report and human-readable summary."""

from dataclasses import dataclass, field
import json
from pathlib import Path

from .config import CATEGORIES


@dataclass
class Move:
    file: str
    category: str
    destination: str
    status: str


@dataclass
class Report:
    source: Path
    dry_run: bool
    processed: int = 0
    moved_by_category: dict[str, int] = field(
        default_factory=lambda: dict.fromkeys(CATEGORIES, 0)
    )
    ignored: list[str] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    moves: list[Move] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "source": str(self.source),
            "dry_run": self.dry_run,
            "processed": self.processed,
            "moved_by_category": self.moved_by_category,
            "ignored": self.ignored,
            "errors": self.errors,
            "moves": [vars(move) for move in self.moves],
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }

    def save_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.as_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def summary(self) -> str:
        action = "Planned" if self.dry_run else "Moved"
        counts = "\n".join(
            f"  {category}: {count}"
            for category, count in self.moved_by_category.items()
            if count
        )
        return (
            f"Processed: {self.processed}\n"
            f"{action} by category:\n{counts or '  None'}\n"
            f"Ignored: {len(self.ignored)}"
            + (f" ({', '.join(self.ignored)})" if self.ignored else "")
            + f"\nErrors: {len(self.errors)}"
            + "".join(f"\n  {item['file']}: {item['error']}" for item in self.errors)
            + f"\nElapsed: {self.elapsed_seconds:.3f}s"
        )
