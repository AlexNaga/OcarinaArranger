"""Simple disk cache for computed preview data."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from ocarina_gui.preview import PreviewData
from ocarina_gui.settings import TransformSettings
from ocarina_tools.events import NoteEvent
from shared.tempo import TempoChange

logger = logging.getLogger(__name__)

_CACHE_DIR = Path.home() / ".ocarina_arranger" / "cache"


def _cache_key(input_path: str, settings: TransformSettings) -> str:
    hasher = hashlib.sha256()
    hasher.update(input_path.encode())
    try:
        stat = Path(input_path).stat()
        hasher.update(str(stat.st_mtime_ns).encode())
        hasher.update(str(stat.st_size).encode())
    except OSError:
        pass
    hasher.update(repr(settings).encode())
    return hasher.hexdigest()[:16]


def load_cached_preview(input_path: str, settings: TransformSettings) -> Optional[PreviewData]:
    key = _cache_key(input_path, settings)
    cache_file = _CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        return PreviewData(
            original_events=tuple(NoteEvent(**e) for e in data["original_events"]),
            arranged_events=tuple(NoteEvent(**e) for e in data["arranged_events"]),
            pulses_per_quarter=data["pulses_per_quarter"],
            beats=data["beats"],
            beat_type=data["beat_type"],
            original_range=tuple(data["original_range"]),
            arranged_range=tuple(data["arranged_range"]),
            tempo_bpm=data["tempo_bpm"],
            tempo_changes=tuple(TempoChange(**t) for t in data["tempo_changes"]),
        )
    except Exception:
        logger.debug("Preview cache miss (corrupt): %s", cache_file, exc_info=True)
        return None


def save_preview_cache(input_path: str, settings: TransformSettings, preview: PreviewData) -> None:
    key = _cache_key(input_path, settings)
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _CACHE_DIR / f"{key}.json"
    try:
        data = {
            "original_events": [_note_to_dict(e) for e in preview.original_events],
            "arranged_events": [_note_to_dict(e) for e in preview.arranged_events],
            "pulses_per_quarter": preview.pulses_per_quarter,
            "beats": preview.beats,
            "beat_type": preview.beat_type,
            "original_range": list(preview.original_range),
            "arranged_range": list(preview.arranged_range),
            "tempo_bpm": preview.tempo_bpm,
            "tempo_changes": [{"tick": t.tick, "tempo_bpm": t.tempo_bpm} for t in preview.tempo_changes],
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")
        logger.info("Preview cached: %s", cache_file.name)
    except Exception:
        logger.debug("Failed to write preview cache", exc_info=True)


def _note_to_dict(e: NoteEvent) -> dict:
    return {
        "onset": e.onset,
        "duration": e.duration,
        "midi": e.midi,
        "program": e.program,
        "tied_durations": list(e.tied_durations),
        "is_grace": e.is_grace,
        "grace_type": e.grace_type,
    }
