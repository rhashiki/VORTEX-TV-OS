"""Contract tests using disposable Git projects, never a real BSP or device.

The orchestration fixtures deliberately contain a tiny Makefile and fake host
version commands. A passing fixture is not evidence of an Android compilation.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools/build_full_platform.py'
spec = importlib.util.spec_from_file_location('full_platform_driver', SCRIPT)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class DriverContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='vortex-driver-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bsp = self.root / 'bsp with spaces'
        self.project = self.bsp / 'build'
        self.project.mkdir(parents=True)
        self.control = self.root / 'control'
        self.control.mkdir()
        self.patches = self.control / 'patches'
        self.patches.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('config', 'core.autocrlf', 'false')
        self.original = 'VALUE := original\n' + '# context\n' * 24
        (self.project / 'tune.mk').write_text(self.original)
        (self.project / 'sub').mkdir()
        (self.project / 'sub/second.mk').write_text('ACTIVE := no\n')
        (self.project / 'envsetup.sh').write_text(
            'lunch() { test "$1" = vortex_rk322x_sd_box-eng; '
            'printf selected > "$OUT_DIR/fixture-lunch"; }\n')
        (self.project / '.gitignore').write_text('ignored/\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture baseline')
        self.pin = self.git('rev-parse', 'HEAD').decode().strip()
        (self.project / 'tune.mk').write_text(self.original.replace('original', 'first'))
        (self.project / 'sub/second.mk').write_text('ACTIVE := yes\n')
        self.first = self.patches / 'first.patch'
        self.first.write_bytes(self.git('diff', '--binary'))
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture patch one')
        (self.project / 'tune.mk').write_text(self.original.replace('original', 'second'))
        self.second = self.patches / 'second.patch'
        self.second.write_bytes(self.git('diff', '--binary'))
        # Destructive reset is confined to this disposable fixture project.
        self.git('reset', '--hard', self.pin)
        self.overlay = self.control / 'rom/platform-reference/vortex-r6-rockchip-experimental.xml'
        self.overlay.parent.mkdir(parents=True)
        self.overlay.write_text('<manifest><project name="fixture-build" path="build" revision="' + self.pin + '"/></manifest>')
        self.plan = self.control / 'rom/product/full-platform-patches.json'
        self.plan.parent.mkdir(parents=True, exist_ok=True)
        self.plan.write_text(json.dumps({'schema_version': 1, 'projects': {
            'build': {'patches': ['patches/first.patch', 'patches/second.patch']}}}))
        self.profile = self.control / 'rom/product/rk322x_sd_box'
        self.profile.mkdir()
        (self.profile / 'AndroidProducts.mk').write_text(
            'ifeq ($(LOCAL_DIR),device/vortex/vortex_rk322x_sd_box)\n'
            'PRODUCT_MAKEFILES := $(LOCAL_DIR)/vortex_rk322x_sd_box.mk\nendif\n')
        (self.profile / 'vortex_rk322x_sd_box.mk').write_text('PRODUCT_DEVICE := vortex_rk322x_sd_box\n')
        self.jdk = self.root / 'fixture-jdk'
        (self.jdk / 'bin').mkdir(parents=True)
        self.executable(self.jdk / 'bin/java', '#!/bin/sh\nprintf \'openjdk version "1.8.fixture"\\n\' >&2\n')
        self.executable(self.jdk / 'bin/javac', '#!/bin/sh\nprintf \'javac 1.8.fixture\\n\'\n')
        self.python2 = self.root / 'fixture-python2'
        self.executable(self.python2, '#!/bin/sh\nprintf \'Python 2.7.fixture\\n\'\n')
        self.out = self.root / 'out'
        self.logs = self.root / 'logs'
        (self.bsp / 'Makefile').write_text('droid:\n\t@printf compiled-fixture > "$(OUT_DIR)/fixture-built"\n')

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.project, stderr=subprocess.PIPE)

    def executable(self, path, text):
        path.write_text(text)
        path.chmod(0o755)

    def verify(self, **kwargs):
        return driver.verify_project(self.project, self.pin, [self.first, self.second], **kwargs)

    def cli(self, *extra):
        command = ['python3', str(SCRIPT), '--bsp-root', str(self.bsp), '--vortex-root', str(self.control),
                   '--jdk-home', str(self.jdk), '--python2', str(self.python2), '--out-dir', str(self.out),
                   '--log-dir', str(self.logs), '--min-free-gib', '0', *extra]
        return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

    def test_pristine_and_exact_prefix_are_resumable(self):
        self.assertEqual(self.verify()['applied_prefix'], 0)
        self.git('apply', str(self.first))
        self.assertEqual(self.verify()['applied_prefix'], 1)
        self.git('apply', str(self.second))
        self.assertEqual(self.verify()['applied_prefix'], 2)

    def test_partial_patch_is_rejected(self):
        (self.project / 'tune.mk').write_text(self.original.replace('original', 'first'))
        with self.assertRaises(driver.Blocked):
            self.verify()

    def test_wrong_pinned_revision_is_rejected(self):
        with self.assertRaises(driver.Blocked):
            driver.verify_project(self.project, '0' * 40, [])

    def test_staged_changes_are_rejected(self):
        self.git('apply', str(self.first))
        self.git('add', '.')
        with self.assertRaises(driver.Blocked):
            self.verify()

    def test_unrelated_tracked_changes_are_rejected(self):
        (self.project / 'envsetup.sh').write_text('exit 99\n')
        with self.assertRaises(driver.Blocked):
            self.verify()

    def test_assume_unchanged_cannot_hide_source_changes(self):
        self.git('update-index', '--assume-unchanged', 'tune.mk')
        (self.project / 'tune.mk').write_text('hidden\n')
        with self.assertRaises(driver.Blocked):
            self.verify()

    def test_default_preflight_does_not_execute_fsmonitor(self):
        helper = self.root / 'fsmonitor-helper'
        marker = self.root / 'fsmonitor-ran'
        self.executable(helper, '#!/bin/sh\nprintf ran > "' + str(marker) + '"\n')
        self.git('config', 'core.fsmonitor', str(helper))
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(marker.exists())

    def test_default_preflight_does_not_execute_clean_filter(self):
        helper = self.root / 'clean-helper'
        marker = self.root / 'clean-ran'
        self.executable(helper, '#!/bin/sh\nprintf ran > "' + str(marker) + '"\ncat\n')
        # Attribute is an actual pinned fixture input, not an unknown file.
        (self.project / '.gitattributes').write_text('tune.mk filter=sideeffect\n')
        self.git('add', '.gitattributes')
        self.git('commit', '-qm', 'fixture with clean-filter attribute')
        self.pin = self.git('rev-parse', 'HEAD').decode().strip()
        self.overlay.write_text('<manifest><project name="fixture-build" path="build" revision="' + self.pin + '"/></manifest>')
        self.git('config', 'filter.sideeffect.clean', str(helper))
        # Force a timestamp change without changing its content.
        os.utime(self.project / 'tune.mk', ns=(1, 1))
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(marker.exists())

    def test_replacement_refs_cannot_substitute_an_unpinned_commit(self):
        (self.project / 'envsetup.sh').write_text('exit 99 # unpinned fixture content\n')
        self.git('add', 'envsetup.sh')
        self.git('commit', '-qm', 'unpinned replacement fixture')
        evil = self.git('rev-parse', 'HEAD').decode().strip()
        self.git('replace', self.pin, evil)
        self.git('reset', '--hard', self.pin)
        self.assertEqual(self.git('rev-parse', 'HEAD').decode().strip(), self.pin)
        self.assertEqual(self.cli('--run').returncode, 2)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.logs.exists())

    def test_skip_worktree_is_rejected(self):
        self.git('update-index', '--skip-worktree', 'tune.mk')
        with self.assertRaises(driver.Blocked):
            self.verify()

    def test_ignored_build_definition_is_rejected(self):
        (self.project / 'ignored').mkdir()
        (self.project / 'ignored/Android.mk').write_text('$(error unexpected)\n')
        with self.assertRaises(driver.Blocked):
            self.verify()

    def test_untracked_inputs_are_rejected(self):
        (self.project / 'other.h').write_text('unreviewed\n')
        with self.assertRaises(driver.Blocked):
            self.verify()

    def test_declared_generated_header_is_inventoried(self):
        (self.project / 'version.h').write_text('fixture generated header\n')
        result = self.verify(generated=('version.h',))
        self.assertEqual(result['observed_generated_inputs']['version.h']['size_bytes'], 25)

    def test_generated_header_cannot_be_a_symlink(self):
        (self.project / 'version.h').symlink_to(self.project / 'tune.mk')
        with self.assertRaises(driver.Blocked):
            self.verify(generated=('version.h',))

    def test_patch_touched_source_cannot_be_a_symlink(self):
        (self.project / 'tune.mk').unlink()
        (self.project / 'tune.mk').symlink_to(self.project / 'sub/second.mk')
        with self.assertRaises(driver.Blocked):
            self.verify()

    def test_product_requires_real_directory_guard(self):
        (self.profile / 'AndroidProducts.mk').write_text('PRODUCT_MAKEFILES := bad\n')
        result = self.cli()
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.out.exists())

    def test_product_device_identity_must_match_destination(self):
        (self.profile / 'vortex_rk322x_sd_box.mk').write_text('PRODUCT_DEVICE := generic\n')
        self.assertEqual(self.cli().returncode, 2)

    def test_existing_product_is_not_overwritten(self):
        dest = self.bsp / driver.DESTINATION
        dest.mkdir(parents=True)
        (dest / 'owned.txt').write_text('keep me')
        self.assertEqual(self.cli('--run').returncode, 2)
        self.assertEqual((dest / 'owned.txt').read_text(), 'keep me')
        self.assertEqual(self.verify()['applied_prefix'], 0)

    def test_product_destination_cannot_be_a_regular_file(self):
        dest = self.bsp / driver.DESTINATION
        dest.parent.mkdir(parents=True)
        dest.write_text('owned file')
        self.assertEqual(self.cli('--run').returncode, 2)
        self.assertEqual(dest.read_text(), 'owned file')
        self.assertEqual(self.verify()['applied_prefix'], 0)

    def test_product_destination_special_child_is_rejected(self):
        dest = self.bsp / driver.DESTINATION
        dest.mkdir(parents=True)
        os.mkfifo(dest / 'Android.mk')
        self.assertEqual(self.cli('--run').returncode, 2)
        self.assertEqual(self.verify()['applied_prefix'], 0)

    def test_template_special_child_is_rejected(self):
        os.mkfifo(self.profile / 'Android.mk')
        self.assertEqual(self.cli('--run').returncode, 2)
        self.assertEqual(self.verify()['applied_prefix'], 0)

    def test_default_check_only_preserves_bsp_and_output(self):
        before = self.git('status', '--porcelain')
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git('status', '--porcelain'), before)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.logs.exists())
        self.assertFalse((self.bsp / driver.DESTINATION).exists())
        self.assertIn(b'pinned_inputs_only_not_module_closure_or_boot_approval', result.stdout)

    def test_failed_preflight_does_not_apply_first_patch(self):
        (self.project / 'envsetup.sh').write_text('unexpected mutation\n')
        self.assertEqual(self.cli('--run').returncode, 2)
        self.assertEqual((self.project / 'tune.mk').read_text(), self.original)
        self.assertFalse(self.logs.exists())

    def test_duplicate_overlay_path_is_rejected(self):
        self.overlay.write_text('<manifest><project name="one" path="build" revision="' + self.pin + '"/>'
                                '<project name="two" path="build" revision="' + self.pin + '"/></manifest>')
        self.assertEqual(self.cli().returncode, 2)

    def test_overlay_cannot_escape_bsp_root(self):
        self.overlay.write_text('<manifest><project name="escape" path="../outside" revision="' + self.pin + '"/></manifest>')
        self.assertEqual(self.cli().returncode, 2)

    def test_source_project_symlink_cannot_escape_bsp_root(self):
        moved = self.root / 'moved-build'
        self.project.rename(moved)
        self.project.symlink_to(moved, target_is_directory=True)
        self.assertEqual(self.cli().returncode, 2)

    def test_output_directory_cannot_overlap_sources(self):
        self.assertEqual(self.cli('--out-dir', str(self.project / 'out')).returncode, 2)

    def test_output_path_cannot_be_a_regular_file(self):
        self.out.write_text('preserve output file')
        self.assertEqual(self.cli('--run').returncode, 2)
        self.assertEqual(self.out.read_text(), 'preserve output file')
        self.assertEqual(self.verify()['applied_prefix'], 0)

    def test_log_directory_cannot_overlap_product_destination(self):
        path = self.bsp / driver.DESTINATION / 'logs'
        self.assertEqual(self.cli('--run', '--log-dir', str(path)).returncode, 2)
        self.assertEqual(self.verify()['applied_prefix'], 0)
        self.assertFalse(path.exists())

    def test_unknown_output_directory_is_not_reused(self):
        self.out.mkdir()
        (self.out / 'existing').write_text('preserve')
        self.assertEqual(self.cli('--run').returncode, 2)
        self.assertEqual((self.out / 'existing').read_text(), 'preserve')

    def test_wrong_javac_version_is_rejected(self):
        self.executable(self.jdk / 'bin/javac', '#!/bin/sh\nprintf \'javac 11.fixture\\n\'\n')
        self.assertEqual(self.cli('--run').returncode, 2)

    def test_real_shell_and_make_orchestration_fixture(self):
        result = self.cli('--run')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.out / 'fixture-lunch').read_text(), 'selected')
        self.assertEqual((self.out / 'fixture-built').read_text(), 'compiled-fixture')
        self.assertEqual(self.verify()['applied_prefix'], 2)
        report = json.loads((self.logs / 'result.json').read_text())
        self.assertEqual(report['status'], 'build_command_succeeded')
        self.assertEqual(report['complete_rom_validation'], 'not_performed')
        self.assertEqual(report['resolved_source_lock']['status'], 'not_available')
        self.assertIn('no resolved lock fabricated', report['resolved_source_lock']['reason'])

    def test_nonzero_build_result_is_recorded(self):
        (self.bsp / 'Makefile').write_text('droid:\n\t@exit 7\n')
        result = self.cli('--run')
        self.assertNotEqual(result.returncode, 0)
        report = json.loads((self.logs / 'result.json').read_text())
        self.assertEqual(report['status'], 'build_command_failed')
        self.assertNotEqual(report['returncode'], 0)

    def test_same_input_marker_allows_a_separate_resume_log(self):
        self.assertEqual(self.cli('--run').returncode, 0)
        result = self.cli('--run', '--log-dir', str(self.root / 'resume-logs'))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_changed_kernel_rejects_stale_output_marker(self):
        image = self.root / 'Image'
        image.write_bytes(b'fixture kernel one')
        self.assertEqual(self.cli('--run', '--kernel-image', str(image)).returncode, 0)
        image.write_bytes(b'fixture kernel two')
        result = self.cli('--kernel-image', str(image))
        self.assertEqual(result.returncode, 2)

    def test_nonfinite_reserve_and_unbounded_jobs_are_rejected(self):
        for extra in (('--min-free-gib', 'nan'), ('--min-free-gib', 'inf'), ('--jobs', '100')):
            with self.subTest(extra=extra):
                self.assertEqual(self.cli(*extra).returncode, 2)


if __name__ == '__main__':
    unittest.main()
