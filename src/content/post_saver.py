from __future__ import annotations

from pathlib import Path


GENERATED_DIR = Path("data/generated")
LATEST_DIR = GENERATED_DIR / "latest"
ARCHIVE_DIR = GENERATED_DIR / "archive"


def ensure_output_dirs() -> None:
    LATEST_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def save_post(filename: str, content: str) -> Path:
    """
    Save/overwrite the latest version of a post.
    """
    ensure_output_dirs()

    path = LATEST_DIR / filename
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def save_post_archive(run_timestamp: str, filename: str, content: str) -> Path:
    """
    Save a timestamped archived copy of a post for this run.
    """
    ensure_output_dirs()

    safe_ts = (
        run_timestamp.replace(":", "-")
        .replace("+00:00", "Z")
        .replace("T", "_")
    )

    run_dir = ARCHIVE_DIR / safe_ts
    run_dir.mkdir(parents=True, exist_ok=True)

    path = run_dir / filename
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def save_both(run_timestamp: str, filename: str, content: str) -> tuple[Path, Path]:
    """
    Save both latest and archived copies.
    """
    latest_path = save_post(filename, content)
    archive_path = save_post_archive(run_timestamp, filename, content)
    return latest_path, archive_path

