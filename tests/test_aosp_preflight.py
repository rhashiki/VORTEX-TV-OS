"""Preflight rejection and read-only behavior; fixtures are not real BSPs."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("aosp_preflight", ROOT / "tools/aosp_preflight.py")
PREFLIGHT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREFLIGHT)


class PreflightChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.bsp = self.directory / "bsp"
        self.bsp.mkdir()
        self.lock = self.directory / "resolved.xml"
        self.lock.write_text('<manifest><project name="example" revision="' + "a" * 40 + '"/></manifest>')
        self.jdk = self.directory / "test-jdk"
        (self.jdk / "bin").mkdir(parents=True)
        self.write_tool("java", 'openjdk version "1.8.0_432"')
        self.write_tool("javac", "javac 1.8.0_432")

    def write_tool(self, name, output):
        path = self.jdk / "bin" / name
        path.write_text("#!/bin/sh\nprintf '%s\\n' '" + output + "' >&2\n")
        path.chmod(0o755)

    def populate(self):
        for relative in PREFLIGHT.REFERENCE_FILES:
            path = self.bsp / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("reference fixture\n")
        (self.bsp / "build/core/version_defaults.mk").write_text(
            "PLATFORM_VERSION := 7.1.2\nPLATFORM_SDK_VERSION := 25\n")
        (self.bsp / "kernel/Makefile").write_text(
            "VERSION = 3\nPATCHLEVEL = 10\nSUBLEVEL = 104\n")
        (self.bsp / "build/envsetup.sh").write_text(
            "#!/bin/sh\ntouch '" + str(self.directory / "must-not-exist") + "'\n")

    def run_cli(self, bsp=None, lock=True):
        args = [sys.executable, str(ROOT / "tools/aosp_preflight.py"), str(bsp or self.bsp), "--json"]
        if lock:
            args += ["--manifest-lock", str(self.lock)]
        result = subprocess.run(args, env={**os.environ, "JAVA_HOME": str(self.jdk)},
                                capture_output=True, text=True, timeout=30)
        return result.returncode, json.loads(result.stdout)

    def blocked(self, report):
        return {item["check"] for item in report["checks"] if item["status"] == "blocked"}

    def test_absent_bsp_fails_without_creating_it(self):
        path = self.directory / "absent"
        code, report = self.run_cli(path)
        self.assertEqual(code, 2)
        self.assertIn("bsp_root", self.blocked(report))
        self.assertFalse(path.exists())
        self.assertEqual(report["inventory"], [])

    def test_incomplete_tree_lists_missing_vendor_and_kernel(self):
        path = self.bsp / "build/envsetup.sh"
        path.parent.mkdir()
        path.write_text("reference fixture\n")
        code, report = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("vendor/rockchip/rk322x/device-vendor.mk", self.blocked(report))
        self.assertIn("vendor/rockchip/rk322x/Android.mk", self.blocked(report))
        self.assertIn("kernel/arch/arm/boot/Image", self.blocked(report))
        self.assertEqual([item["path"] for item in report["inventory"]], ["build/envsetup.sh"])

    def test_fixture_checks_are_read_only_and_never_approve_hardware(self):
        self.populate()
        def snapshot():
            return {p.relative_to(self.bsp).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                    for p in self.bsp.rglob("*") if p.is_file()}
        before = snapshot()
        code, report = self.run_cli()
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "preflight_only")
        self.assertEqual(report["hardware_validation"], "not_performed")
        self.assertEqual(report["rom_build_validation"], "not_performed")
        self.assertEqual(snapshot(), before)
        self.assertFalse((self.directory / "must-not-exist").exists())
        inventory = {item["path"]: item for item in report["inventory"]}
        expected = hashlib.sha256((self.bsp / "build/envsetup.sh").read_bytes()).hexdigest()
        self.assertEqual(inventory["build/envsetup.sh"]["sha256"], expected)

    def test_wrong_platform_is_blocked(self):
        self.populate()
        (self.bsp / "build/core/version_defaults.mk").write_text(
            "PLATFORM_VERSION := 7.1.1\nPLATFORM_SDK_VERSION := 25\n")
        code, report = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("android_version", self.blocked(report))

    def test_missing_lock_is_not_replaced_by_checkout_manifest(self):
        self.populate()
        code, report = self.run_cli(lock=False)
        self.assertEqual(code, 2)
        self.assertIn("resolved_manifest", self.blocked(report))

    def test_branch_or_unresolved_include_is_not_a_pinned_lock(self):
        self.populate()
        for content in ('<manifest><project name="example" revision="main"/></manifest>',
                        '<manifest><include name="other.xml"/><project name="example" revision="' + "a" * 40 + '"/></manifest>'):
            with self.subTest(manifest=content):
                self.lock.write_text(content)
                code, report = self.run_cli()
                self.assertEqual(code, 2)
                self.assertIn("resolved_manifest", self.blocked(report))

    def test_jre_or_mixed_compiler_does_not_pass_as_jdk8(self):
        self.populate()
        for version in (None, "javac 11.0.32.1"):
            with self.subTest(compiler=version):
                compiler = self.jdk / "bin/javac"
                if version is None:
                    compiler.unlink()
                else:
                    self.write_tool("javac", version)
                code, report = self.run_cli()
                self.assertEqual(code, 2)
                self.assertIn("jdk8", self.blocked(report))

    def test_nested_project_must_also_have_pinned_revision(self):
        self.populate()
        self.lock.write_text('<manifest><project name="parent" revision="' + "a" * 40 +
                             '"><project name="child" revision="main"/></project></manifest>')
        code, report = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("resolved_manifest", self.blocked(report))

    def test_symlink_escape_is_not_read_or_hashed(self):
        self.populate()
        outside = self.directory / "outside"
        outside.write_text("must not be read\n")
        path = self.bsp / "kernel/arch/arm/boot/Image"
        path.unlink()
        path.symlink_to(outside)
        code, report = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("kernel/arch/arm/boot/Image", self.blocked(report))
        self.assertNotIn("kernel/arch/arm/boot/Image", [item["path"] for item in report["inventory"]])


if __name__ == "__main__":
    unittest.main()
