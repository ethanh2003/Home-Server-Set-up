import importlib.util
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "recording_watchdog.py"
)
SYSTEMD_DIR = Path(__file__).resolve().parents[1] / "systemd"


def load_watchdog():
    if not MODULE_PATH.exists():
        raise AssertionError(f"watchdog module is missing: {MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("recording_watchdog", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def recording_path(
    root: Path, when: datetime, camera: str, name: str
) -> Path:
    path = root / when.strftime("%Y-%m-%d") / when.strftime("%H") / camera / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"segment")
    os.utime(path, (when.timestamp(), when.timestamp()))
    return path


class SegmentTests(unittest.TestCase):
    def test_newest_segment_checks_current_and_previous_hour(self):
        watchdog = load_watchdog()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = datetime(2026, 7, 25, 0, 0, 20, tzinfo=timezone.utc)
            expected = recording_path(
                root,
                now - timedelta(seconds=30),
                "camera_a",
                "59.50.mp4",
            )

            self.assertEqual(
                watchdog.newest_segment(root, "camera_a", now),
                expected,
            )

    def test_zero_byte_segment_is_invalid(self):
        watchdog = load_watchdog()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.mp4"
            path.touch()
            now = datetime.now(timezone.utc)

            self.assertFalse(watchdog.segment_is_valid(path, now, 90))


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.watchdog = load_watchdog()
        self.now = datetime(2026, 7, 25, 2, 0, 0, tzinfo=timezone.utc)
        self.state = {"first_stale_at": {}, "last_restart_at": 0}

    def evaluate(self, camera, segment, when=None):
        return self.watchdog.evaluate_camera(
            camera=camera,
            segment=segment,
            now=when or self.now,
            max_age=90,
            confirm_after=30,
            cooldown=600,
            state=self.state,
        )

    def test_healthy_recording_clears_prior_stale_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            segment = recording_path(
                root,
                self.now - timedelta(seconds=10),
                "camera_a",
                "59.50.mp4",
            )
            self.state["first_stale_at"]["camera_a"] = (
                self.now - timedelta(seconds=60)
            ).timestamp()

            result = self.evaluate("camera_a", segment)

            self.assertEqual(result.action, "healthy")
            self.assertNotIn("camera_a", self.state["first_stale_at"])

    def test_first_stale_observation_requests_confirmation(self):
        result = self.evaluate("camera_a", None)

        self.assertEqual(result.action, "confirm")
        self.assertEqual(
            self.state["first_stale_at"]["camera_a"],
            self.now.timestamp(),
        )

    def test_confirmed_stale_observation_requests_restart(self):
        self.evaluate("camera_a", None)

        result = self.evaluate(
            "camera_a",
            None,
            self.now + timedelta(seconds=30),
        )

        self.assertEqual(result.action, "restart")

    def test_recent_restart_suppresses_another_restart(self):
        self.state["first_stale_at"]["camera_a"] = (
            self.now - timedelta(seconds=60)
        ).timestamp()
        self.state["last_restart_at"] = (
            self.now - timedelta(seconds=300)
        ).timestamp()

        result = self.evaluate("camera_a", None)

        self.assertEqual(result.action, "cooldown")

    def test_stale_camera_does_not_hide_healthy_camera(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            healthy_segment = recording_path(
                root,
                self.now - timedelta(seconds=10),
                "camera_b",
                "59.50.mp4",
            )

            stale = self.evaluate("camera_a", None)
            healthy = self.evaluate("camera_b", healthy_segment)

            self.assertEqual(stale.action, "confirm")
            self.assertEqual(healthy.action, "healthy")

    def test_state_round_trips_json(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            self.state["first_stale_at"]["camera_a"] = self.now.timestamp()

            self.watchdog.save_state(state_path, self.state)

            self.assertEqual(
                self.watchdog.load_state(state_path),
                self.state,
            )


class FakeRunner:
    def __init__(self, responses=None):
        self.calls = []
        self.responses = list(responses or [])

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if self.responses:
            return self.responses.pop(0)
        return subprocess.CompletedProcess(command, 0, "", "")


class ExternalBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.watchdog = load_watchdog()

    def test_restart_uses_only_the_scoped_compose_command(self):
        runner = FakeRunner()
        compose_file = Path("/srv/frigate/docker-compose.yml")

        succeeded = self.watchdog.restart_frigate(
            compose_file,
            runner=runner,
            dry_run=False,
        )

        self.assertTrue(succeeded)
        self.assertEqual(
            runner.calls[0][0],
            [
                "docker",
                "compose",
                "-f",
                str(compose_file),
                "restart",
                "frigate",
            ],
        )

    def test_probe_rejects_non_native_video(self):
        payload = {
            "streams": [
                {
                    "codec_name": "h264",
                    "codec_type": "video",
                    "width": 1280,
                    "height": 720,
                },
                {"codec_name": "aac", "codec_type": "audio"},
            ]
        }
        runner = FakeRunner(
            [
                subprocess.CompletedProcess(
                    ["ffprobe"],
                    0,
                    json.dumps(payload),
                    "",
                )
            ]
        )

        self.assertFalse(
            self.watchdog.probe_segment(Path("/recordings/camera.mp4"), runner)
        )

    def test_probe_accepts_native_h264_video_with_audio(self):
        payload = {
            "streams": [
                {
                    "codec_name": "h264",
                    "codec_type": "video",
                    "width": 2560,
                    "height": 1920,
                },
                {"codec_name": "aac", "codec_type": "audio"},
            ]
        }
        runner = FakeRunner(
            [
                subprocess.CompletedProcess(
                    ["ffprobe"],
                    0,
                    json.dumps(payload),
                    "",
                )
            ]
        )

        self.assertTrue(
            self.watchdog.probe_segment(Path("/recordings/camera.mp4"), runner)
        )

    def test_confirmed_dry_run_reports_restart_without_running_docker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "state.json"
            lock_path = root / "lock"
            now = datetime.now(timezone.utc)
            state_path.write_text(
                json.dumps(
                    {
                        "first_stale_at": {
                            "camera_a": (now - timedelta(seconds=60)).timestamp()
                        },
                        "last_restart_at": 0,
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            exit_code = self.watchdog.main(
                [
                    "--camera",
                    "camera_a",
                    "--recordings-root",
                    str(root / "recordings"),
                    "--compose-file",
                    str(root / "docker-compose.yml"),
                    "--state-file",
                    str(state_path),
                    "--lock-file",
                    str(lock_path),
                    "--dry-run",
                ],
                stdout=output,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn(
                "docker compose -f "
                f"{root / 'docker-compose.yml'} restart frigate",
                output.getvalue(),
            )


class SystemdUnitTests(unittest.TestCase):
    def test_units_are_hardened_and_scheduled_every_30_seconds(self):
        service_path = SYSTEMD_DIR / "frigate-recording-watchdog.service"
        timer_path = SYSTEMD_DIR / "frigate-recording-watchdog.timer"
        self.assertTrue(service_path.exists(), f"missing {service_path}")
        self.assertTrue(timer_path.exists(), f"missing {timer_path}")

        service = service_path.read_text(encoding="utf-8")
        timer = timer_path.read_text(encoding="utf-8")

        self.assertIn("Type=oneshot", service)
        self.assertIn("NoNewPrivileges=true", service)
        self.assertIn("ProtectSystem=strict", service)
        self.assertIn("RuntimeDirectoryPreserve=yes", service)
        self.assertIn("OnUnitActiveSec=30s", timer)
        self.assertIn("Persistent=true", timer)
        self.assertNotIn("rtsp://", service + timer)


if __name__ == "__main__":
    unittest.main()
