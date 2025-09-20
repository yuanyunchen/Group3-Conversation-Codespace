"""Utility helpers for benchmarking pipeline."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


def slugify(value: str) -> str:
    allowed = []
    for char in value.replace(" ", "_"):
        if char.isalnum() or char in {"_", "-"}:
            allowed.append(char.lower())
    slug = "".join(allowed)
    return slug or "run"


def timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
