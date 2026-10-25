"""Official-source rejection and generic ZIP regressions; no official media fixture.

Synthetic PNGs exercise only the generic encoder and frame validation helpers.
These tests do not substitute a video or bypass the production SHA-256 gate.
"""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/bootanimation_from_video.py"
SPEC = importlib.util.spec_from_file_location("bootanimation_from_video", SCRIPT)
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


class OfficialBootSourceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.video = self.root / "unapproved.mp4"
        self.video.write_bytes(b"Not the approved Vortex source video")

    def test_unapproved_source_does_not_create_destination_directory(self):
        output = self.root / "not-created" / "bootanimation.zip"
        with mock.patch.object(generator.subprocess, "run") as ffmpeg:
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                generator.build(self.video, output, official=True)
        ffmpeg.assert_not_called()
        self.assertFalse(output.parent.exists())

    def test_source_video_cannot_be_used_as_output(self):
        original = self.video.read_bytes()
        with mock.patch.object(generator.subprocess, "run") as ffmpeg:
            with self.assertRaisesRegex(ValueError, "must not replace the source"):
                generator.build(self.video, self.video, official=True)
        ffmpeg.assert_not_called()
        self.assertEqual(self.video.read_bytes(), original)

    def test_unapproved_source_preserves_existing_destination(self):
        output = self.root / "bootanimation.zip"
        output.write_bytes(b"previous artifact")
        with mock.patch.object(generator.subprocess, "run") as ffmpeg:
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                generator.build(self.video, output, official=True)
        ffmpeg.assert_not_called()
        self.assertEqual(output.read_bytes(), b"previous artifact")

    def test_official_mode_rejects_non_twelve_fps_before_encoding(self):
        output = self.root / "bootanimation.zip"
        with mock.patch.object(generator.subprocess, "run") as ffmpeg:
            with self.assertRaisesRegex(ValueError, "requires 12 fps"):
                generator.build(self.video, output, fps=24, official=True)
        ffmpeg.assert_not_called()
        self.assertFalse(output.exists())

    def test_cli_official_flag_rejects_unapproved_source(self):
        output = self.root / "bootanimation.zip"
        output.write_bytes(b"previous artifact")
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.video),
                                 "--official", "--out", str(output)],
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SHA-256 mismatch", result.stderr)
        self.assertEqual(output.read_bytes(), b"previous artifact")

    def test_official_frame_validator_rejects_wrong_count(self):
        with self.assertRaisesRegex(ValueError, "exactly 48 frames"):
            generator._validate_official_frames([self.root / "frame.png"] * 47)

    def test_official_frame_validator_rejects_wrong_size(self):
        frame = self.root / "small.png"
        Image.new("RGB", (16, 9)).save(frame)
        with self.assertRaisesRegex(ValueError, "1280x720"):
            generator._validate_official_frames([frame] * 48)

    def test_generic_encoder_keeps_last_frame_loop_and_stored_zip(self):
        output = self.root / "bootanimation.zip"
        output.write_bytes(b"previous artifact")

        def extract_synthetic_frames(command, **kwargs):
            directory = Path(command[-1]).parent
            for index, color in enumerate(("red", "blue"), 1):
                Image.new("RGB", (1280, 720), color).save(directory / f"{index:04d}.png")

        with mock.patch.object(generator.subprocess, "run", side_effect=extract_synthetic_frames):
            size = generator.build(self.video, output)
        self.assertEqual(size, output.stat().st_size)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(set(archive.namelist()),
                             {"desc.txt", "part0/0000.png", "part0/0001.png", "part1/0000.png"})
            self.assertEqual(archive.read("desc.txt"),
                             b"1280 720 12\np 1 0 part0\np 0 0 part1\n")
            self.assertEqual(archive.read("part1/0000.png"), archive.read("part0/0001.png"))
            self.assertTrue(all(info.compress_type == zipfile.ZIP_STORED
                                for info in archive.infolist()))
        self.assertFalse(list(self.root.glob(".vortex-boot-*")))

    def test_invalid_extracted_frame_preserves_destination_and_removes_staging(self):
        output = self.root / "bootanimation.zip"
        output.write_bytes(b"previous artifact")

        def extract_invalid_frame(command, **kwargs):
            (Path(command[-1]).parent / "0001.png").write_bytes(b"not an image")

        with mock.patch.object(generator.subprocess, "run", side_effect=extract_invalid_frame):
            with self.assertRaises(OSError):
                generator.build(self.video, output)
        self.assertEqual(output.read_bytes(), b"previous artifact")
        self.assertFalse(list(self.root.glob(".vortex-boot-*")))


if __name__ == "__main__":
    unittest.main()
