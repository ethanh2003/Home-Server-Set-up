#!/usr/bin/env python3
"""Monitor Frigate recording freshness and recover stale capture pipelines."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from typing import Callable, Sequence, TextIO


@dataclass(frozen=True)
class CameraResult:
    camera: str
    action: str
    segment: Path | None


Runner = Callable[..., subprocess.CompletedProcess[str]]


def hour_directories(root: Path, now: datetime) -> list[Path]:
    return [
        root / stamp.strftime("%Y-%m-%d") / stamp.strftime("%H")
        for stamp in (now, now - timedelta(hours=1))
    ]


def newest_segment(root: Path, camera: str, now: datetime) -> Path | None:
    matches = [
        path
        for hour in hour_directories(root, now)
        for path in (hour / camera).glob("*.mp4")
        if path.is_file()
    ]
    return max(matches, key=lambda path: path.stat().st_mtime, default=None)


def segment_is_valid(
    path: Path | None,
    now: datetime,
    max_age: int,
) -> bool:
    if path is None or path.stat().st_size == 0:
        return False
    age = now.timestamp() - path.stat().st_mtime
    return 0 <= age <= max_age


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"first_stale_at": {}, "last_restart_at": 0}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def evaluate_camera(
    *,
    camera: str,
    segment: Path | None,
    now: datetime,
    max_age: int,
    confirm_after: int,
    cooldown: int,
    state: dict[str, Any],
) -> CameraResult:
    first_stale_at = state.setdefault("first_stale_at", {})
    state.setdefault("last_restart_at", 0)

    if segment_is_valid(segment, now, max_age):
        first_stale_at.pop(camera, None)
        return CameraResult(camera, "healthy", segment)

    now_timestamp = now.timestamp()
    stale_timestamp = first_stale_at.get(camera)
    if stale_timestamp is None:
        first_stale_at[camera] = now_timestamp
        return CameraResult(camera, "confirm", segment)

    if now_timestamp - stale_timestamp < confirm_after:
        return CameraResult(camera, "confirm", segment)

    last_restart_at = state["last_restart_at"]
    if last_restart_at and now_timestamp - last_restart_at < cooldown:
        return CameraResult(camera, "cooldown", segment)

    return CameraResult(camera, "restart", segment)


def restart_frigate(
    compose_file: Path,
    *,
    runner: Runner = subprocess.run,
    dry_run: bool,
) -> bool:
    command = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "restart",
        "frigate",
    ]
    if dry_run:
        return True
    result = runner(
        command,
        capture_output=True,
        text=True,
        timeout=180,
    )
    return result.returncode == 0


def probe_segment(
    segment: Path,
    runner: Runner = subprocess.run,
) -> bool:
    result = runner(
        [
            "/usr/bin/ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_name,codec_type,width,height",
            "-of",
            "json",
            str(segment),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return False
    try:
        streams = json.loads(result.stdout)["streams"]
    except (KeyError, TypeError, json.JSONDecodeError):
        return False
    video_is_native = any(
        stream.get("codec_type") == "video"
        and stream.get("codec_name") == "h264"
        and stream.get("width") == 2560
        and stream.get("height") == 1920
        for stream in streams
    )
    audio_is_present = any(
        stream.get("codec_type") == "audio" for stream in streams
    )
    return video_is_native and audio_is_present


def wait_for_container_health(
    *,
    timeout: int,
    runner: Runner = subprocess.run,
) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = runner(
            [
                "docker",
                "inspect",
                "frigate",
                "--format={{.State.Health.Status}}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip() == "healthy":
            return True
        time.sleep(5)
    return False


def wait_for_recordings(
    *,
    root: Path,
    cameras: Sequence[str],
    not_before: float,
    timeout: int,
) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        now = datetime.now().astimezone()
        segments = {
            camera: newest_segment(root, camera, now) for camera in cameras
        }
        if all(
            segment is not None
            and segment.stat().st_mtime >= not_before
            and segment_is_valid(segment, now, 90)
            and probe_segment(segment)
            for segment in segments.values()
        ):
            return True
        time.sleep(5)
    return False


def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recover stale Frigate recording pipelines."
    )
    parser.add_argument("--camera", action="append", required=True)
    parser.add_argument("--recordings-root", type=Path, required=True)
    parser.add_argument("--compose-file", type=Path, required=True)
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--lock-file", type=Path, required=True)
    parser.add_argument("--max-age", type=int, default=90)
    parser.add_argument("--confirm-after", type=int, default=30)
    parser.add_argument("--cooldown", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(arguments)


def main(
    arguments: Sequence[str] | None = None,
    *,
    stdout: TextIO = sys.stdout,
) -> int:
    args = parse_args(arguments)
    args.lock_file.parent.mkdir(parents=True, exist_ok=True)

    with args.lock_file.open("a+", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("watchdog already running", file=stdout)
            return 0

        now = datetime.now().astimezone()
        state = load_state(args.state_file)
        results = []
        for camera in args.camera:
            segment = newest_segment(args.recordings_root, camera, now)
            result = evaluate_camera(
                camera=camera,
                segment=segment,
                now=now,
                max_age=args.max_age,
                confirm_after=args.confirm_after,
                cooldown=args.cooldown,
                state=state,
            )
            results.append(result)
            print(
                f"camera={camera} action={result.action} "
                f"segment={segment if segment else 'missing'}",
                file=stdout,
            )

        save_state(args.state_file, state)
        if not any(result.action == "restart" for result in results):
            return 0 if all(
                result.action == "healthy" for result in results
            ) else 1

        command_text = (
            f"docker compose -f {args.compose_file} restart frigate"
        )
        if args.dry_run:
            print(f"dry-run: {command_text}", file=stdout)
            return 1

        restart_started = now.timestamp()
        state["last_restart_at"] = restart_started
        save_state(args.state_file, state)
        print(f"recovery: {command_text}", file=stdout)
        if not restart_frigate(
            args.compose_file,
            runner=subprocess.run,
            dry_run=False,
        ):
            print("recovery failed: Frigate restart command failed", file=stdout)
            return 1

        if not wait_for_container_health(timeout=120):
            print("recovery failed: Frigate did not become healthy", file=stdout)
            return 1

        if not wait_for_recordings(
            root=args.recordings_root,
            cameras=args.camera,
            not_before=restart_started,
            timeout=120,
        ):
            print(
                "recovery failed: recordings did not resume and validate",
                file=stdout,
            )
            return 1

        for camera in args.camera:
            state["first_stale_at"].pop(camera, None)
        save_state(args.state_file, state)
        print("recovery succeeded: all recordings are fresh", file=stdout)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
