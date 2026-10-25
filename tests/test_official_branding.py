"""Import invariants with synthetic JPEGs; no official art is claimed available."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("official_branding", ROOT / "tools/import_official_branding.py")
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class OfficialBrandingChecks(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.repository = self.directory / "repository"
        self.repository.mkdir()
        self.inputs = {}
        self.fixture_specs = []
        for asset in IMPORTER.ASSETS:
            # Only this test's in-process synthetic manifest uses fixture hashes.
            # The production CLI has no expected-hash override or force switch.
            image = Image.new("RGB", asset["size"], color=(0, 10, 20))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            data = buffer.getvalue()
            path = self.directory / (asset["name"] + ".png")
            path.write_bytes(data)
            self.inputs[asset["name"]] = path
            self.fixture_specs.append({**asset, "sha256": hashlib.sha256(data).hexdigest()})

    def snapshot(self):
        return {path.relative_to(self.repository).as_posix():
                (path.read_bytes(), path.stat().st_mtime_ns)
                for path in self.repository.rglob("*") if path.is_file()}

    def prepare_fixture(self):
        with mock.patch.object(IMPORTER, "ASSETS", tuple(self.fixture_specs)):
            return IMPORTER.prepare_import(self.inputs, self.repository)

    def test_production_cli_rejects_substitute_without_writing(self):
        args = [sys.executable, str(ROOT / "tools/import_official_branding.py"),
                "--repo-root", str(self.repository)]
        for name, path in self.inputs.items():
            args += ["--" + name, str(path)]
        result = subprocess.run(args, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        error = json.loads(result.stderr)
        self.assertEqual(error["status"], "blocked")
        self.assertIn("SHA-256 mismatch", error["error"])
        self.assertEqual(list(self.repository.iterdir()), [])

    def test_missing_last_source_leaves_no_partial_import(self):
        self.inputs["logo"].unlink()
        with self.assertRaisesRegex(ValueError, "logo: original file is absent"):
            self.prepare_fixture()
        self.assertEqual(list(self.repository.iterdir()), [])

    def test_preview_is_rejected_without_writing(self):
        preview = self.inputs["square"]
        Image.new("RGB", (96, 96)).save(preview, format="WEBP")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            IMPORTER.prepare_import(self.inputs, self.repository)
        self.assertEqual(list(self.repository.iterdir()), [])

    def test_final_input_mismatch_leaves_no_partial_import(self):
        self.inputs["logo"].write_bytes(b"incorrect final input")
        with self.assertRaisesRegex(ValueError, "logo: SHA-256 mismatch"):
            self.prepare_fixture()
        self.assertEqual(list(self.repository.iterdir()), [])

    def test_check_only_does_not_write_and_reports_output_hashes(self):
        args = ["--repo-root", str(self.repository), "--check-only"]
        for name, path in self.inputs.items():
            args += ["--" + name, str(path)]
        with mock.patch.object(IMPORTER, "ASSETS", tuple(self.fixture_specs)), \
                mock.patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(IMPORTER.main(args), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "checked")
        self.assertEqual(len(report["assets"]), 3)
        self.assertEqual(report["assets"][2]["resource"]["dimensions"], [480, 202])
        self.assertEqual(list(self.repository.iterdir()), [])

    def test_import_preserves_original_bytes_and_resizes_without_white_background(self):
        root, plan, report = self.prepare_fixture()
        IMPORTER.write_import(root, plan)
        for item in report["assets"]:
            original = (self.repository / item["source"]["path"]).read_bytes()
            self.assertEqual(original, self.inputs[item["name"]].read_bytes())
            with Image.open(self.repository / item["resource"]["path"]) as resource:
                self.assertEqual(resource.size, tuple(item["resource"]["dimensions"]))
                self.assertEqual(resource.format, "PNG")
                self.assertLess(max(resource.getpixel((0, 0))), 30)
        before = self.snapshot()
        root, plan, _ = self.prepare_fixture()
        IMPORTER.write_import(root, plan)
        self.assertEqual(self.snapshot(), before)

    def test_conflicting_output_does_not_overwrite_or_add_other_files(self):
        conflict = self.repository / IMPORTER.ASSETS[-1]["resource"]
        conflict.parent.mkdir(parents=True)
        conflict.write_bytes(b"preserve existing work")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            self.prepare_fixture()
        self.assertEqual(self.snapshot(), before)

    def test_symlink_output_outside_repository_is_not_written(self):
        outside = self.directory / "outside"
        outside.mkdir()
        (self.repository / "branding").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink escapes"):
            self.prepare_fixture()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual([p.name for p in self.repository.iterdir()], ["branding"])

    def test_write_error_rolls_back_published_files(self):
        root, plan, _ = self.prepare_fixture()
        real_link = IMPORTER.os.link
        calls = []

        def fail_second(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError("simulated disk failure")
            real_link(source, destination)

        with mock.patch.object(IMPORTER.os, "link", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "simulated disk failure"):
                IMPORTER.write_import(root, plan)
        self.assertEqual(list(self.repository.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
