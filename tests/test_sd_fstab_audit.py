"""Static SD fstab checks; these fixtures do not represent a bootable image."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/audit_sd_fstab.py"
SPEC = importlib.util.spec_from_file_location("audit_sd_fstab", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
PREFIX = "/dev/block/platform/ff500000.rksdmmc/by-name/"
FSTAB = """# Synthetic static-profile fixture, not a board image.
{p}system /system ext4 ro,noatime,nodiratime,noauto_da_alloc wait,resize
{p}cache /cache ext4 noatime,nodiratime,nosuid,nodev,noauto_da_alloc,discard wait
{p}metadata /metadata ext4 noatime,nodiratime,nosuid,nodev,noauto_da_alloc,discard wait,check
{p}userdata /data ext4 noatime,nodiratime,nosuid,nodev,noauto_da_alloc,discard,errors=panic wait,check,encryptable=/metadata/key_file
{p}misc /misc emmc defaults defaults
/devices/ff580000.usb* auto vfat defaults voldmanaged=usb:auto
/devices/ff5c0000.usb* auto vfat defaults voldmanaged=usb:auto
/devices/ff5d0000.usb* auto vfat defaults voldmanaged=usb:auto
/devices/usb* auto vfat defaults voldmanaged=usb:auto
/dev/block/zram0 none swap defaults zramsize=533413200
""".format(p=PREFIX)


class SdFstabChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.fstab = self.directory / "fstab.sd"
        self.fstab.write_text(FSTAB)

    def run_cli(self, path=None):
        result = subprocess.run([sys.executable, str(SCRIPT), str(path or self.fstab), "--json"],
                                capture_output=True, text=True, timeout=5)
        return result.returncode, json.loads(result.stdout)

    def assert_blocked(self, text, message=None):
        self.fstab.write_text(text)
        code, report = self.run_cli()
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "blocked")
        if message:
            self.assertTrue(any(message in item["message"] for item in report["checks"]), report)
        return report

    def test_profile_pass_is_read_only_and_never_approves_boot(self):
        before = (self.fstab.read_bytes(), self.fstab.stat().st_mtime_ns,
                  sorted(p.name for p in self.directory.iterdir()))
        code, report = self.run_cli()
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "fstab_only")
        self.assertEqual(report["input"]["sha256"], hashlib.sha256(before[0]).hexdigest())
        self.assertEqual(report["input"]["size_bytes"], len(before[0]))
        self.assertEqual(report["external_controller"], "ff500000.rksdmmc")
        self.assertEqual(report["source_profile"]["revision"], "f33a129bfab6d9cc87184ee3bf032224801fa446")
        self.assertEqual(report["rom_build_validation"], "not_performed")
        self.assertEqual(report["hardware_validation"], "not_performed")
        self.assertTrue(any("internal storage" in item for item in report["limits"]))
        self.assertEqual((self.fstab.read_bytes(), self.fstab.stat().st_mtime_ns,
                          sorted(p.name for p in self.directory.iterdir())), before)

    def test_only_required_sd_partitions_are_sufficient(self):
        self.fstab.write_text("\n".join(line for line in FSTAB.splitlines()
                                        if not line.startswith(("/devices/", "/dev/block/zram"))))
        self.assertEqual(self.run_cli()[0], 0)

    def test_rk3229_sdk_reference_must_be_explicit_and_rejects_old_controller(self):
        # This is a source combination check, not identification of a TV Box.
        profile = "rk3229-sdk-sd-reference"
        self.assertEqual(AUDIT.inspect(self.fstab, profile=profile)["status"], "blocked")
        self.fstab.write_text(FSTAB.replace("ff500000.rksdmmc", "30000000.rksdmmc"))
        self.assertEqual(self.run_cli()[0], 2)
        report = AUDIT.inspect(self.fstab, profile=profile)
        self.assertEqual(report["status"], "fstab_only")
        self.assertEqual(report["external_controller"], "30000000.rksdmmc")
        self.assertEqual(report["hardware_validation"], "not_performed")
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.fstab),
                                 "--profile", profile, "--json"],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0)

    def test_sdk_profile_still_rejects_emmc_and_boot_sd_automount(self):
        for source in ("30020000.rksdmmc", "ff500000.rksdmmc"):
            text = FSTAB.replace("ff500000.rksdmmc", "30000000.rksdmmc")
            text = text.replace("30000000.rksdmmc/by-name/userdata", source + "/by-name/userdata")
            self.fstab.write_text(text)
            self.assertEqual(AUDIT.inspect(self.fstab, profile="rk3229-sdk-sd-reference")["status"], "blocked")
        self.fstab.write_text(FSTAB.replace("ff500000.rksdmmc", "30000000.rksdmmc") +
                             "/devices/30000000.rksdmmc/mmc_host* auto auto defaults voldmanaged=sdcard1:auto\n")
        self.assertEqual(AUDIT.inspect(self.fstab, profile="rk3229-sdk-sd-reference")["status"], "blocked")

    def test_unknown_profile_is_rejected_instead_of_accepting_arbitrary_controller(self):
        with self.assertRaises(ValueError):
            AUDIT.inspect(self.fstab, profile="whatever-device")

    def test_internal_data_sources_are_blocked(self):
        for replacement in ("/dev/block/platform/ff520000.rksdmmc/by-name/userdata",
                            "/dev/block/rknand_userdata", "/dev/block/mmcblk0p7"):
            with self.subTest(source=replacement):
                self.assert_blocked(FSTAB.replace(PREFIX + "userdata", replacement), "SD source for /data")

    def test_missing_required_partition_is_blocked(self):
        text = "\n".join(line for line in FSTAB.splitlines() if " /metadata " not in line)
        self.assert_blocked(text, "found 0")

    def test_duplicate_mount_point_is_blocked(self):
        self.assert_blocked(FSTAB + PREFIX + "userdata /data ext4 defaults wait\n", "found 2")

    def test_read_write_system_and_conflicting_flags_are_blocked(self):
        for flags in ("rw,noatime", "noatime", "ro,rw,noatime"):
            with self.subTest(flags=flags):
                self.assert_blocked(FSTAB.replace("ro,noatime,nodiratime,noauto_da_alloc", flags),
                                    "must be mounted ro")

    def test_reference_boot_sd_automount_is_blocked(self):
        automount = "/devices/ff500000.rksdmmc/mmc_host* auto auto defaults voldmanaged=sdcard1:auto\n"
        self.assert_blocked(FSTAB + automount, "removable/formattable")

    def test_other_sources_mounts_and_extra_columns_are_blocked(self):
        for extra in ("/dev/block/rknand_system /vendor ext4 ro wait\n",
                      PREFIX + "boot /boot emmc defaults defaults\n",
                      "/dev/null /other ext4 ro wait\n",
                      PREFIX + "system /system ext4 ro wait unexpected\n"):
            with self.subTest(extra=extra):
                self.assert_blocked(FSTAB + extra)

    def test_wrong_filesystem_type_and_misc_flags_are_blocked(self):
        for original, replacement in (("/data ext4", "/data f2fs"),
                                      ("/misc emmc defaults defaults", "/misc emmc rw wait")):
            with self.subTest(replacement=replacement):
                self.assert_blocked(FSTAB.replace(original, replacement))

    def test_unrecognized_or_duplicate_flags_are_blocked(self):
        for original, replacement in (("wait,resize", "wait,unknown_flag"),
                                      ("wait,resize", "wait,wait"),
                                      ("ro,noatime", "ro,noatime,noatime")):
            with self.subTest(replacement=replacement):
                self.assert_blocked(FSTAB.replace(original, replacement))

    def test_usb_source_does_not_allow_another_mount_or_fs_mgr_action(self):
        self.assert_blocked(FSTAB.replace("auto vfat defaults voldmanaged=usb:auto",
                                         "/data ext4 defaults wait", 1))

    def test_optional_sources_may_not_be_duplicated(self):
        for duplicate in ("/devices/usb* auto vfat defaults voldmanaged=usb:auto\n",
                          "/dev/block/zram0 none swap defaults zramsize=1\n"):
            with self.subTest(duplicate=duplicate):
                self.assert_blocked(FSTAB + duplicate, "Duplicate optional source")

    def test_invalid_zram_size_is_blocked(self):
        for size in ("0", "-1", "1,other=2", str(2 ** 32 + 1), "1" * 5000, "١"):
            with self.subTest(size=size):
                self.assert_blocked(FSTAB.replace("zramsize=533413200", "zramsize=" + size))

    def test_comments_are_ignored_but_malformed_lines_are_blocked(self):
        self.fstab.write_text(FSTAB + "# /dev/block/rknand_system /system ext4 rw defaults\n")
        self.assertEqual(self.run_cli()[0], 0)
        self.assert_blocked(FSTAB + "not enough columns\n", "five Android fstab columns")

    def test_missing_file_and_directory_are_blocked_without_creating_output(self):
        for path in (self.directory / "absent", self.directory):
            with self.subTest(path=path):
                before = sorted(p.name for p in self.directory.iterdir())
                code, report = self.run_cli(path)
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "blocked")
                self.assertEqual(sorted(p.name for p in self.directory.iterdir()), before)

    def test_symlink_input_or_parent_is_not_followed(self):
        linked = self.directory / "linked"
        linked.symlink_to(self.fstab)
        parent = self.directory / "parent-link"
        parent.symlink_to(self.directory, target_is_directory=True)
        for path in (linked, parent / self.fstab.name):
            with self.subTest(path=path):
                code, report = self.run_cli(path)
                self.assertEqual(code, 2)
                self.assertIn("Symlink", report["checks"][0]["message"])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO fixture needs POSIX")
    def test_fifo_is_rejected_without_blocking(self):
        fifo = self.directory / "fifo"
        os.mkfifo(fifo)
        code, report = self.run_cli(fifo)
        self.assertEqual(code, 2)
        self.assertIn("special files are not read", report["checks"][0]["message"])

    def test_device_path_is_rejected_before_open(self):
        with mock.patch.object(AUDIT.os, "open") as opened:
            report = AUDIT.inspect("/dev/null")
        opened.assert_not_called()
        self.assertEqual(report["status"], "blocked")

    def test_oversized_input_is_rejected_before_open(self):
        self.fstab.write_bytes(b"#" * (1024 * 1024 + 1))
        with mock.patch.object(AUDIT.os, "open") as opened:
            report = AUDIT.inspect(self.fstab)
        opened.assert_not_called()
        self.assertEqual(report["status"], "blocked")
        self.assertIn("1 MiB", report["checks"][0]["message"])

    def test_invalid_utf8_and_control_characters_are_blocked(self):
        for data in (FSTAB.encode() + b"\xff", FSTAB.encode() + b"\0",
                     FSTAB.replace("system /system", "system\u00a0/system").encode(),
                     ("\u00a0" + FSTAB).encode(),
                     FSTAB.replace("wait,resize\n", "wait,resize\u2028").encode()):
            with self.subTest(data=data[-1:]):
                self.fstab.write_bytes(data)
                code, report = self.run_cli()
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
