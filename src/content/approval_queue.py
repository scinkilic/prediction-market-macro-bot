from __future__ import annotations

import shutil
from pathlib import Path


GENERATED_DIR = Path("data/generated")
LATEST_DIR = GENERATED_DIR / "latest"
APPROVED_DIR = GENERATED_DIR / "approved"


def ensure_approval_dirs() -> None:
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)


def list_latest_posts() -> list[Path]:
    if not LATEST_DIR.exists():
        return []
    return sorted([p for p in LATEST_DIR.iterdir() if p.is_file()])


def approve_post(filename: str) -> Path:
    ensure_approval_dirs()

    source = LATEST_DIR / filename
    if not source.exists():
        raise FileNotFoundError(f"Latest post not found: {source}")

    destination = APPROVED_DIR / filename
    shutil.copy2(source, destination)
    return destination


def clear_approved_posts() -> None:
    ensure_approval_dirs()
    for path in APPROVED_DIR.iterdir():
        if path.is_file():
            path.unlink()

