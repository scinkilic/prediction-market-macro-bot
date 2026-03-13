from __future__ import annotations

from pathlib import Path


GENERATED_DIR = Path("data/generated")


def save_post(filename: str, content: str) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    path = GENERATED_DIR / filename
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path

