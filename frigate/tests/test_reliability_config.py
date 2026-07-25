from pathlib import Path
import unittest

import yaml


STACK_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = STACK_DIR / "config" / "config.yml"
COMPOSE_PATH = STACK_DIR / "docker-compose.yml"
CAMERAS = (
    "living_room_-_dog_view",
    "living_room_-_couch_view",
)


class FrigateReliabilityConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.compose = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))

    def test_recording_uses_local_restream_and_vaapi(self):
        ffmpeg = self.config.get("ffmpeg", {})
        self.assertEqual(ffmpeg.get("hwaccel_args"), "preset-vaapi")
        self.assertIn(
            ffmpeg.get("output_args", {}).get("record"),
            {
                "preset-record-generic-audio-copy",
                "preset-record-generic-audio-aac",
            },
        )

        for camera in CAMERAS:
            entry = self.config["cameras"][camera]
            self.assertFalse(entry["detect"].get("enabled", True))
            self.assertEqual(len(entry["ffmpeg"]["inputs"]), 1)
            input_config = entry["ffmpeg"]["inputs"][0]
            self.assertEqual(
                input_config["path"],
                f"rtsp://127.0.0.1:8554/{camera}",
            )
            self.assertEqual(
                input_config.get("input_args"),
                "preset-rtsp-restream",
            )
            self.assertEqual(
                set(input_config["roles"]),
                {"record", "detect", "audio"},
            )

    def test_go2rtc_keeps_one_nonempty_upstream_per_camera(self):
        streams = self.config.get("go2rtc", {}).get("streams", {})
        for camera in CAMERAS:
            self.assertIn(camera, streams)
            self.assertEqual(len(streams[camera]), 1)
            self.assertTrue(streams[camera][0])

    def test_compose_has_reliability_resource_policy(self):
        service = self.compose["services"]["frigate"]
        self.assertEqual(service["cpus"], "2.0")
        self.assertEqual(service["mem_limit"], "3g")
        self.assertEqual(service["mem_reservation"], "1536m")
        self.assertEqual(service["memswap_limit"], "3g")
        self.assertEqual(service["pids_limit"], 768)
        self.assertEqual(service["shm_size"], "512mb")
        self.assertNotIn("privileged", service)
        self.assertLessEqual(
            set(service.get("cap_add", [])),
            {"PERFMON"},
        )


if __name__ == "__main__":
    unittest.main()
