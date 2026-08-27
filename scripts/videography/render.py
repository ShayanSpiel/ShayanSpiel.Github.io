"""Renderer: turn a captured webm into a polished MP4 with ffmpeg.

Usage:
  python3 scripts/videography/render.py INPUT.webm --out OUTPUT.mp4 [--crf 20] [--fps 30]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def ffmpeg_bin() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise SystemExit("ffmpeg not found on PATH")
    return path


def render(webm: str, out: str, crf: int = 20, fps: int = 30) -> Path:
    src, dest = Path(webm), Path(out)
    if not src.exists():
        raise SystemExit(f"capture missing: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_bin(), "-y", "-i", str(src),
        "-vf", f"fps={fps},format=yuv420p",
        "-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
        "-movflags", "+faststart", "-an", str(dest),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"ffmpeg failed rc={proc.returncode}")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="webm capture")
    ap.add_argument("--out", required=True, help="output mp4 path")
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()
    dest = render(args.input, args.out, crf=args.crf, fps=args.fps)
    print(f"rendered: {dest} ({dest.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
