#!/usr/bin/env python3
"""Build the five-minute Mail-Shop cartoon tutorial as an MP4.

Run from the repository root with the optional media dependencies available in
/tmp/mail_shop_tools. The build is deterministic and can be rerun after editing
frames or narration.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCENES = ROOT / "scenes"
AUDIO = ROOT / "audio"
BUILD = ROOT / ".build"
OUTPUT = ROOT / "mail_shop_tutorial_5min.mp4"
FULL_AUDIO = BUILD / "full_narration.mp3"
SILENT_VIDEO = BUILD / "silent_video.mp4"

# The narration is 348.75 seconds before a gentle 1.1625x timing adjustment.
# The resulting audio is exactly 300 seconds, distributed across 15 storyboard
# frames. Counts are integers so the final video is exactly 9,000 frames at 30fps.
FRAME_COUNTS = [517, 517, 518, 649, 650, 650, 586, 586, 587, 581, 581, 580, 666, 666, 666]
assert sum(FRAME_COUNTS) == 9000

AUDIO_FILES = [
    AUDIO / "01-welcome.mp3",
    AUDIO / "02-account.mp3",
    AUDIO / "03-inbox.mp3",
    AUDIO / "04-otp.mp3",
    AUDIO / "05-settings.mp3",
]


def ffmpeg_path() -> str:
    candidate = Path("/tmp/mail_shop_tools/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2")
    if candidate.exists():
        return str(candidate)
    env = os.environ.get("FFMPEG")
    if env and Path(env).exists():
        return env
    raise SystemExit("ffmpeg binary not found; install imageio-ffmpeg into /tmp/mail_shop_tools first")


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def build_audio(ff: str) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    labels = [f"[{i}:a]" for i in range(len(AUDIO_FILES))]
    concat_inputs = "".join(labels)
    filter_graph = f"{concat_inputs}concat=n={len(AUDIO_FILES)}:v=0:a=1,atempo=1.1625,aresample=44100:async=1[aout]"
    cmd = [ff, "-y", "-hide_banner", "-loglevel", "error"]
    for path in AUDIO_FILES:
        cmd += ["-i", str(path)]
    cmd += [
        "-filter_complex", filter_graph,
        "-map", "[aout]",
        "-ar", "44100",
        "-ac", "2",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        str(FULL_AUDIO),
    ]
    run(cmd)


def build_scene_segments(ff: str) -> list[Path]:
    seg_dir = BUILD / "segments"
    if seg_dir.exists():
        shutil.rmtree(seg_dir)
    seg_dir.mkdir(parents=True, exist_ok=True)
    segments: list[Path] = []
    for index, frames in enumerate(FRAME_COUNTS, start=1):
        source = SCENES / f"scene_{index:02d}.png"
        target = seg_dir / f"segment_{index:02d}.mp4"
        fade_out = max(0.3, (frames - 10) / 30)
        vf = (
            "zoompan=z='min(zoom+0.00075,1.045)':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=30,"
            "fade=t=in:st=0:d=0.30,"
            f"fade=t=out:st={fade_out:.3f}:d=0.30,format=yuv420p"
        )
        run([
            ff, "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-framerate", "30", "-i", str(source),
            "-frames:v", str(frames),
            "-vf", vf,
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "24",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            str(target),
        ])
        segments.append(target)
    concat_file = BUILD / "segments.txt"
    concat_file.write_text("\n".join(f"file '{path.as_posix()}'" for path in segments) + "\n")
    run([
        ff, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c", "copy",
        "-movflags", "+faststart",
        str(SILENT_VIDEO),
    ])
    return segments


def mux(ff: str) -> None:
    run([
        ff, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(SILENT_VIDEO),
        "-i", str(FULL_AUDIO),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(OUTPUT),
    ])


def main() -> None:
    missing = [str(p) for p in [*AUDIO_FILES, *(SCENES / f"scene_{i:02d}.png" for i in range(1, 16))] if not p.exists()]
    if missing:
        raise SystemExit("Missing media inputs:\n" + "\n".join(missing))
    ff = ffmpeg_path()
    build_audio(ff)
    build_scene_segments(ff)
    mux(ff)
    # Keep the useful source assets and narration, but remove encoded segment
    # intermediates so the repository stays small and reruns stay clean.
    shutil.rmtree(BUILD / "segments", ignore_errors=True)
    (BUILD / "segments.txt").unlink(missing_ok=True)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / (1024 * 1024):.1f} MiB)")


if __name__ == "__main__":
    main()
