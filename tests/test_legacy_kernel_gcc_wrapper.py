"""Exercise the copied Python 3 host wrapper with isolated fake compilers.

No kernel source, APK or ROM is compiled by these tests. The allowed diagnostic
is a concrete case from the original wrapper, not generated from its whitelist.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "tools/legacy_kernel_gcc_wrapper.py"
FAKE_COMPILER = '''import argparse
import os
from pathlib import Path
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("-o", required=True)
parser.add_argument("--diagnostic", default="")
parser.add_argument("--exit-code", type=int, default=0)
parser.add_argument("--finish-late-marker")
args = parser.parse_args()
# Most cases write before the diagnostic; the late-writer case recreates the
# object afterwards to exercise the original wrapper's removal race.
Path(args.o).write_bytes(b"isolated fake object\\n")
if args.diagnostic:
    sys.stderr.write(args.diagnostic + "\\n")
    sys.stderr.flush()
if args.finish_late_marker:
    time.sleep(0.2)
    Path(args.o).write_bytes(b"late fake object\\n")
    Path(args.finish_late_marker).write_text(str(os.getpid()), encoding="utf-8")
sys.exit(args.exit_code)
'''


class LegacyKernelGccWrapperTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="vortex wrapper test ")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.compiler = self.directory / "fake compiler.py"
        self.compiler.write_text(FAKE_COMPILER, encoding="utf-8")
        self.output = self.directory / "kernel object.o"

    def run_wrapper(self, diagnostic="", exit_code=0, late_marker=None):
        command = [sys.executable, str(WRAPPER), sys.executable, str(self.compiler),
                   "-o", str(self.output), "--diagnostic", diagnostic,
                   "--exit-code", str(exit_code)]
        if late_marker is not None:
            command += ["--finish-late-marker", str(late_marker)]
        # The copied port decodes compiler stderr using Python's text mode.
        # Force UTF-8 for both child interpreters and the captured diagnostics.
        environment = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
        return subprocess.run(command, cwd=self.directory, env=environment,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="strict", timeout=10)

    def test_forbidden_warning_fails_and_removes_object(self):
        diagnostic = "drivers/example.c:17:5: warning: diagnóstico não permitido [-Wexample]"
        result = self.run_wrapper(diagnostic)
        self.assertEqual(result.returncode, 1)
        self.assertIn(diagnostic, result.stdout)
        self.assertIn("error, forbidden warning: example.c:17", result.stdout)
        self.assertFalse(self.output.exists())

    def test_known_upstream_warning_keeps_success_and_object(self):
        # return_address.c:63 is explicitly allowed by the original kernel
        # wrapper. Keep this fixed even if a future copy changes that list.
        diagnostic = ("arch/arm/kernel/return_address.c:63:2: warning: "
                      "calling '__builtin_return_address' with a nonzero argument")
        result = self.run_wrapper(diagnostic)
        self.assertEqual(result.returncode, 0)
        self.assertIn(diagnostic, result.stdout)
        self.assertNotIn("forbidden warning", result.stdout)
        self.assertEqual(self.output.read_bytes(), b"isolated fake object\n")

    def test_silent_compiler_keeps_success_and_object(self):
        result = self.run_wrapper()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.output.read_bytes(), b"isolated fake object\n")

    def test_multiline_compiler_output_preserves_line_starts(self):
        # mkcompile_h identifies the version using a line beginning with gcc.
        diagnostic = "Using built-in specs.\nTarget: arm-linux-gnueabihf\ngcc version 6.3.1"
        result = self.run_wrapper(diagnostic)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, diagnostic + "\n")
        self.assertEqual(result.stderr, "")

    def test_compiler_failure_code_is_preserved(self):
        result = self.run_wrapper(exit_code=7)
        self.assertEqual(result.returncode, 7)
        self.assertNotIn("forbidden warning", result.stdout)

    def test_late_object_is_removed_after_compiler_finishes(self):
        marker = self.directory / "compiler finished.txt"
        result = self.run_wrapper("drivers/late.c:29:4: warning: late object writer",
                                  late_marker=marker)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.output.exists())
        compiler_pid = int(marker.read_text(encoding="utf-8"))
        # wait() reaps the fake compiler before the wrapper returns.
        with self.assertRaises(ProcessLookupError):
            os.kill(compiler_pid, 0)


if __name__ == "__main__":
    unittest.main()
