#!/usr/bin/env python3
"""Render lightweight animated QA previews from extracted OpenPets pet frames."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

# OpenPets v4.1.0 整行时长；宿主使用等分 CSS steps，GIF 只能以10ms精度近似。
ROW_TIMINGS = {
    "idle": (6, 5500),
    "running-right": (8, 1060),
    "running-left": (8, 1060),
    "waving": (4, 700),
    "jumping": (5, 840),
    "failed": (8, 1220),
    "waiting": (6, 1010),
    "running": (6, 820),
    "review": (6, 1030),
}
IMAGE_SUFFIXES = {".png", ".webp", ".jpg", ".jpeg"}


def gif_durations(frame_count: int, duration_ms: int) -> list[int]:
    if frame_count < 1 or duration_ms < frame_count * 10 or duration_ms % 10:
        raise ValueError("GIF timing needs positive frames and a representable 10ms duration")
    # 舍入累计边界而非逐帧舍入，保持总时长；不把误差集中成末帧停顿。
    boundaries = [round(index * duration_ms / frame_count / 10) * 10 for index in range(frame_count + 1)]
    return [end - start for start, end in zip(boundaries, boundaries[1:])]


ROW_DURATIONS = {state: gif_durations(count, duration) for state, (count, duration) in ROW_TIMINGS.items()}


def frame_files(state_dir: Path) -> list[Path]:
    if not state_dir.is_dir():
        return []
    return sorted(path for path in state_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)


def load_frames(frames_root: Path, state: str, expected_count: int) -> list[Image.Image]:
    files = frame_files(frames_root / state)
    if len(files) != expected_count:
        raise SystemExit(
            f"{state} preview needs {expected_count} frames, found {len(files)} under {frames_root / state}"
        )
    frames = []
    for path in files:
        with Image.open(path) as opened:
            frames.append(opened.convert("RGBA"))
    return frames


def save_preview(frames: list[Image.Image], durations: list[int], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--waiting-duration-ms", type=int, choices=(1010, 2200), default=1010)
    args = parser.parse_args()

    frames_root = Path(args.frames_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    previews = []
    for state, (count, duration) in ROW_TIMINGS.items():
        if state == "waiting":
            duration = args.waiting_duration_ms
        durations = gif_durations(count, duration)
        frames = load_frames(frames_root, state, len(durations))
        output = output_dir / f"{state}.gif"
        save_preview(frames, durations, output)
        previews.append({"state": state, "path": str(output), "frames": len(frames), "duration_ms": duration})

    result = {"ok": True, "output_dir": str(output_dir), "timing_baseline": "OpenPets v4.1.0", "loop": "infinite QA preview; host waving/jumping/failed default to two iterations", "previews": previews}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
