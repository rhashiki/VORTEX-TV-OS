"""Negative input-contract checks; fixtures do not constitute a BSP or ROM."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "tools" / "audit_product_inputs.py"
SPEC = importlib.util.spec_from_file_location("audit_product_inputs", TOOL)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class ProductInputsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "bsp"
        self.root.mkdir()
        self.packages = self.base / "packages.list"
        self.copies = self.base / "copy-files.list"
        self.config = self.base / "config-values.list"
        self.packages.write_text("\n".join(sorted(AUDIT.REQUIRED_PACKAGES)) + "\n")
        self.config.write_text("\n".join(k + "=" + v for k, v in AUDIT.EXPECTED_CONFIG.items()) + "\n")
        self.entries = []
        for index, destination in enumerate(sorted(AUDIT.REQUIRED_DESTINATIONS)):
            source = "inputs/file-%02d" % index
            self.write_source(source, b"<fixture />" if destination.endswith(".xml")
                              else ("synthetic input for " + destination).encode())
            self.entries.append(source + ":" + destination)
        self.write_copies()

    def write_source(self, name, data=b"fixture"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def write_copies(self):
        self.copies.write_text("\n".join(self.entries) + "\n")

    def inspect(self):
        return AUDIT.inspect(self.packages, self.copies, self.config, self.root)

    def assert_blocked(self, check=None):
        report = self.inspect()
        self.assertEqual("blocked", report["status"])
        self.assertEqual("not_performed", report["rom_build_validation"])
        self.assertEqual("not_performed", report["hardware_validation"])
        if check:
            self.assertTrue(any(c["check"] == check and c["status"] == "blocked"
                                for c in report["checks"]), report["checks"])
        return report

    def append_copy(self, source, destination, data=b"fixture"):
        self.write_source(source, data)
        self.entries.append(source + ":" + destination)
        self.write_copies()

    def test_valid_fixture_has_narrow_scope_and_exact_source_hashes(self):
        report = self.inspect()
        self.assertEqual("product_inputs_only", report["status"])
        self.assertEqual("not_performed", report["rom_build_validation"])
        self.assertEqual("not_performed", report["hardware_validation"])
        self.assertTrue(any("transitive dependencies" in text for text in report["limits"]))
        for item in report["copies"]:
            data = (self.root / item["source"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])

    def test_missing_home_or_installer_or_storage_provider_blocks(self):
        original = self.packages.read_text()
        for package in ("VortexHome", "PackageInstaller", "DefaultContainerService", "ExternalStorageProvider"):
            with self.subTest(package=package):
                self.packages.write_text(original.replace(package + "\n", ""))
                self.assert_blocked("required_packages")

    def test_stock_launcher_bluetooth_google_and_recovery_packages_block(self):
        original = self.packages.read_text()
        for package in ("Launcher3", "Bluetooth", "PrebuiltGmsCore", "Phonesky", "recovery",
                        "uncrypt", "applypatch", "gralloc.default", "RkUpdateService", "Provision",
                        "GoogleLoginService", "GooglePartnerSetup"):
            with self.subTest(package=package):
                self.packages.write_text(original + package + "\n")
                self.assert_blocked("forbidden_packages")

    def test_duplicate_inherited_package_is_counted_without_inventing_module_failure(self):
        self.packages.write_text(self.packages.read_text() + "VortexHome\n")
        report = self.inspect()
        self.assertEqual("product_inputs_only", report["status"])
        self.assertEqual(report["package_counts"]["unique"] + 1, report["package_counts"]["entries"])

    def test_missing_false_or_explicit_empty_config_cannot_pass(self):
        original = self.config.read_text()
        for record in ("BOARD_HAVE_BLUETOOTH=false\n", "BOARD_CONNECTIVITY_VENDOR=\n",
                       "TARGET_RELEASETOOLS_EXTENSIONS=\n"):
            with self.subTest(record=record):
                self.config.write_text(original.replace(record, ""))
                self.assert_blocked("config:" + record.split("=", 1)[0])

    def test_wrong_arch_or_product_or_wifi_selection_blocks(self):
        original = self.config.read_text()
        for old, new in (("TARGET_ARCH=arm", "TARGET_ARCH=arm64"),
                         ("TARGET_DEVICE=vortex_rk322x_sd_box", "TARGET_DEVICE=generic"),
                         ("BOARD_WLAN_DEVICE=\n", "BOARD_WLAN_DEVICE=bcmdhd\n")):
            with self.subTest(new=new):
                self.config.write_text(original.replace(old, new))
                self.assert_blocked("config:" + old.split("=", 1)[0])

    def test_duplicate_or_malformed_configuration_records_block(self):
        original = self.config.read_text()
        for record in ("TARGET_ARCH=arm\n", "not an assignment\n"):
            with self.subTest(record=record):
                self.config.write_text(original + record)
                self.assert_blocked("config_record")

    def test_unresolved_inheritance_and_make_tokens_block(self):
        original = self.packages.read_text()
        for marker in ("@inherit:device/common.mk", "$(BAD_MODULE)", "${BAD_MODULE}"):
            with self.subTest(marker=marker):
                self.packages.write_text(original + marker)
                self.assert_blocked("input:packages")

    def test_control_nul_and_invalid_utf8_input_block(self):
        for suffix in (b"\0", b"\x01", b"\xff"):
            with self.subTest(suffix=suffix):
                self.packages.write_bytes(b"VortexHome\n" + suffix)
                self.assert_blocked("input:packages")

    def test_nonmodule_tokens_block(self):
        self.packages.write_text(self.packages.read_text() + "path/to/Module\n")
        self.assert_blocked("package_syntax")

    def test_list_size_limit_blocks(self):
        self.packages.write_bytes(b"x" * (AUDIT.MAX_INPUT_BYTES + 1))
        self.assert_blocked("input:packages")

    def test_symlink_list_or_parent_directory_blocks(self):
        target = self.base / "packages-target"
        self.packages.rename(target)
        self.packages.symlink_to(target)
        self.assert_blocked("input:packages")
        self.packages.unlink()
        target.rename(self.packages)
        alias = self.base / "lists-alias"
        alias.symlink_to(self.base, target_is_directory=True)
        report = AUDIT.inspect(alias / self.packages.name, self.copies, self.config, self.root)
        self.assertEqual("blocked", report["status"])

    def test_fifo_list_is_rejected_without_opening_it(self):
        self.packages.unlink()
        os.mkfifo(self.packages)
        self.assert_blocked("input:packages")

    def test_absolute_parent_backslash_and_alias_copy_paths_block(self):
        original = list(self.entries)
        for bad in ("input:/system/etc/extra", "../input:system/etc/extra",
                    "input:system/../etc/extra", "input:system//etc/extra",
                    "input:system/etc/extra/", "input:system\\etc\\extra",
                    "inputs//file:system/etc/extra"):
            with self.subTest(bad=bad):
                self.entries = original + [bad]
                self.write_copies()
                self.assert_blocked("copy_path")

    def test_invalid_copy_arity_and_owner_block(self):
        original = list(self.entries)
        for bad in ("input", "input:system/etc/extra:a:b", "input:system/etc/extra:owner/child"):
            with self.subTest(bad=bad):
                self.entries = original + [bad]
                self.write_copies()
                self.assert_blocked("copy_record")

    def test_missing_required_copy_blocks(self):
        self.entries.pop()
        self.write_copies()
        self.assert_blocked("required_copies")

    def test_destination_conflict_blocks_even_if_android_keeps_first_source(self):
        destination = self.entries[0].split(":")[1]
        self.append_copy("inputs/alternative", destination)
        self.assert_blocked("copy_conflict")

    def test_same_copy_with_different_owner_is_a_conflict(self):
        self.entries += [self.entries[0] + ":root", self.entries[0] + ":system"]
        self.write_copies()
        self.assert_blocked("copy_conflict")

    def test_repeated_identical_copy_is_not_a_false_conflict(self):
        self.entries.append(self.entries[0])
        self.write_copies()
        self.assertEqual("product_inputs_only", self.inspect()["status"])

    def test_prebuilt_graphics_hal_bluetooth_google_and_updater_copies_block(self):
        original = list(self.entries)
        for destination in ("system/lib/hw/gralloc.rk30board.so",
                            "system/lib/hw/hwcomposer.rk30board.so",
                            "system/lib/hw/gralloc.default.so", "system/etc/firmware/bt.hcd",
                            "system/lib/rtkbt/libplugin.so", "system/priv-app/GmsCore/GmsCore.apk",
                            "system/etc/permissions/com.google.test.xml",
                            "system/lib/librockchip_update_jni.so", "system/bin/install-recovery.sh"):
            with self.subTest(destination=destination):
                self.entries = list(original)
                self.append_copy("inputs/extra", destination)
                self.assert_blocked("copy_policy")

    def test_internal_unknown_and_generic_fstabs_block(self):
        original = list(self.entries)
        for name in ("fstab.rk30board.bootmode.emmc", "fstab.rk30board.bootmode.nand",
                     "fstab.rk30board.bootmode.unknown", "fstab.rk30board"):
            with self.subTest(name=name):
                self.entries = list(original)
                self.append_copy("inputs/extra", "root/" + name)
                self.assert_blocked("copy_policy")

    def test_renamed_internal_fstab_source_cannot_hide_behind_sd_destination(self):
        index = next(i for i, item in enumerate(self.entries)
                     if item.endswith(":root/fstab.rk30board.bootmode.sd"))
        self.write_source("device/fstab.rk30board.bootmode.emmc")
        self.entries[index] = "device/fstab.rk30board.bootmode.emmc:root/fstab.rk30board.bootmode.sd"
        self.write_copies()
        self.assert_blocked("copy_policy")

    def test_bluetooth_directory_at_source_root_is_still_blocked(self):
        self.append_copy("bluetooth/firmware.bin", "system/etc/firmware/firmware.bin")
        self.assert_blocked("copy_policy")

    def test_google_feature_declaration_blocks_even_with_neutral_filename(self):
        self.append_copy("inputs/features", "system/etc/permissions/features.xml",
                         b'<permissions><feature name="GOOGLE_EXPERIENCE" /></permissions>')
        self.assert_blocked("copy_source")

    def test_encoded_google_xml_declarations_cannot_bypass_policy(self):
        original = list(self.entries)
        for data in (b'<permissions><feature name="GOOGLE_&#66;UILD" /></permissions>',
                     '<?xml version="1.0" encoding="utf-16"?><permissions><feature name="GOOGLE_BUILD" /></permissions>'.encode("utf-16"),
                     b'<permissions><library name="com.google.android.example" /></permissions>'):
            with self.subTest(data=data[:50]):
                self.entries = list(original)
                self.append_copy("inputs/encoded-features", "system/etc/permissions/neutral.xml", data)
                self.assert_blocked("copy_source")

    def test_renamed_bluetooth_or_google_source_still_blocks(self):
        original = list(self.entries)
        for source in ("inputs/bt.hcd", "inputs/libbt-vendor.so", "inputs/GmsCore.apk"):
            with self.subTest(source=source):
                self.entries = list(original)
                self.append_copy(source, "system/etc/neutral.bin")
                self.assert_blocked("copy_policy")

    def test_malformed_copied_xml_blocks(self):
        self.append_copy("inputs/broken-xml", "system/etc/permissions/neutral.xml", b"<permissions>")
        self.assert_blocked("copy_source")

    def test_unknown_xml_encoding_blocks_without_traceback(self):
        self.append_copy("inputs/unknown-xml-encoding", "system/etc/permissions/neutral.xml",
                         b'<?xml version="1.0" encoding="vortex-unknown"?><permissions />')
        self.assert_blocked("copy_source")

    def test_missing_source_blocks(self):
        (self.root / self.entries[0].split(":")[0]).unlink()
        self.assert_blocked("copy_source")

    def test_symlink_source_or_fifo_source_blocks(self):
        source = self.root / self.entries[0].split(":")[0]
        original = source.read_bytes()
        source.unlink()
        target = self.write_source("inputs/target", original)
        source.symlink_to(target)
        self.assert_blocked("copy_source")
        source.unlink()
        os.mkfifo(source)
        self.assert_blocked("copy_source")

    def test_resolved_pseudo_filesystem_source_blocks(self):
        alias = self.root / "kernel-fs"
        alias.symlink_to("/proc", target_is_directory=True)
        self.entries.append("kernel-fs/version:system/etc/kernel-fs-version")
        self.write_copies()
        self.assert_blocked("copy_source")

    def test_source_directory_symlink_is_allowed_for_pinned_checkout(self):
        common = self.base / "pinned-core"
        common.mkdir()
        (common / "declared-file").write_bytes(b"genuine checkout bytes in actual use")
        (self.root / "core").symlink_to(common, target_is_directory=True)
        self.entries.append("core/declared-file:system/etc/declared-file")
        self.write_copies()
        self.assertEqual("product_inputs_only", self.inspect()["status"])

    def test_oversized_source_blocks(self):
        source = self.root / self.entries[0].split(":")[0]
        with source.open("wb") as stream:
            stream.truncate(AUDIT.MAX_SOURCE_BYTES + 1)
        self.assert_blocked("copy_source")

    def test_json_cli_exit_codes_and_scoped_output(self):
        args = ["--packages", str(self.packages), "--copy-files", str(self.copies),
                "--config-values", str(self.config), "--bsp-root", str(self.root), "--json"]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = AUDIT.main(args)
        self.assertEqual(0, status)
        self.assertEqual("product_inputs_only", json.loads(output.getvalue())["status"])
        self.packages.write_text("recovery\n")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = AUDIT.main(args)
        self.assertEqual(2, status)
        self.assertEqual("blocked", json.loads(output.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
