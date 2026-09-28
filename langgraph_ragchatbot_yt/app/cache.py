import hashlib
import json
import os
import re
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import urlencode
from urllib.request import urlopen


CACHE_SCHEMA_VERSION = 1
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / "data" / "video_cache"

_lock_guard = threading.Lock()
_video_locks: dict[str, tuple[threading.RLock, int]] = {}
_video_titles: dict[str, str] = {}


def cache_root() -> Path:
    return Path(os.getenv("VIDEO_CACHE_DIR", str(DEFAULT_CACHE_DIR)))


def _video_id_hash(video_id: str) -> str:
    video_key = hashlib.sha256(video_id.encode("utf-8")).hexdigest()
    return video_key


def _safe_video_directory_name(video_id: str, title: str) -> str:
    title_slug = re.sub(r"[^\w.-]+", "_", title.strip(), flags=re.UNICODE)
    title_slug = title_slug.strip("._-")[:80] or "youtube-video"
    safe_id = re.sub(r"[^\w-]+", "_", video_id)[:32]
    return f"{title_slug}--{safe_id}"


def video_cache_dir(video_id: str, video_title: str | None = None) -> Path:
    title = video_title
    if title is None:
        with _lock_guard:
            title = _video_titles.get(video_id)
    if title:
        return cache_root() / _safe_video_directory_name(video_id, title)
    return cache_root() / _video_id_hash(video_id)


def prepare_video_cache(video_id: str, video_title: str | None = None) -> str:
    """Resolve a display title, migrate legacy ID-hash caches, and cache the title."""
    if not video_id:
        raise ValueError("A video_id is required to prepare its cache.")

    with video_processing_lock(video_id):
        supplied_title = (video_title or "").strip()
        legacy_directory = cache_root() / _video_id_hash(video_id)
        with _lock_guard:
            process_title = _video_titles.get(video_id, "")
        legacy_pointer = read_json(legacy_directory / "title.json") or {}
        legacy_metadata = legacy_pointer or read_json(legacy_directory / "metadata.json") or {}
        title = (
            supplied_title
            or process_title
            or str(legacy_metadata.get("title") or "").strip()
        )

        if not title:
            try:
                query = urlencode({
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "format": "json",
                })
                with urlopen(
                    f"https://www.youtube.com/oembed?{query}", timeout=4
                ) as response:
                    title = str(json.load(response).get("title") or "").strip()
            except Exception:
                title = ""
        title = title or video_id

        destination = video_cache_dir(video_id, title)
        previous_directory_name = legacy_pointer.get("directory", "")
        if (
            previous_directory_name
            and Path(previous_directory_name).name == previous_directory_name
        ):
            previous_directory = cache_root() / previous_directory_name
        else:
            previous_directory = legacy_directory
        source_directory = (
            previous_directory
            if previous_directory.exists() and previous_directory != legacy_directory
            else legacy_directory
        )
        if (
            source_directory != destination
            and source_directory.exists()
            and not destination.exists()
        ):
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source_directory, destination)

        with _lock_guard:
            _video_titles[video_id] = title

        metadata = read_json(destination / "metadata.json") or {}
        if metadata.get("title") != title:
            update_video_metadata(video_id, {"title": title}, video_title=title)
        if legacy_directory != destination:
            write_json_atomic(
                legacy_directory / "title.json",
                {
                    "video_id": video_id,
                    "title": title,
                    "directory": destination.name,
                    "cache_schema_version": CACHE_SCHEMA_VERSION,
                },
            )
    return title


@contextmanager
def video_processing_lock(video_id: str) -> Iterator[None]:
    """Serialize processing for one video without blocking other videos."""
    with _lock_guard:
        lock, users = _video_locks.get(video_id, (threading.RLock(), 0))
        _video_locks[video_id] = (lock, users + 1)

    lock.acquire()
    try:
        yield
    finally:
        lock.release()
        with _lock_guard:
            current_lock, users = _video_locks[video_id]
            if users == 1:
                del _video_locks[video_id]
            else:
                _video_locks[video_id] = (current_lock, users - 1)


def read_json(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def write_json_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f"{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            json.dump(value, file, ensure_ascii=False, separators=(",", ":"))
            temp_path = Path(file.name)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def update_video_metadata(
    video_id: str,
    values: dict,
    video_title: str | None = None,
) -> None:
    with video_processing_lock(video_id):
        directory = video_cache_dir(video_id, video_title)
        path = directory / "metadata.json"
        metadata = read_json(path) or {
            "video_id": video_id,
            "cache_schema_version": CACHE_SCHEMA_VERSION,
        }
        if metadata.get("cache_schema_version") != CACHE_SCHEMA_VERSION:
            metadata = {
                "video_id": video_id,
                "cache_schema_version": CACHE_SCHEMA_VERSION,
            }
        metadata.update(values)
        write_json_atomic(path, metadata)