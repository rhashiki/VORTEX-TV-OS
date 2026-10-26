"""Cross-file rejection tests; synthetic inputs never represent a bootable image."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from tools import audit_sd_boot_inputs as AUDIT


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/audit_sd_boot_inputs.py"
CMDLINE = "vmalloc=496M psci=enable storagemedia=sd androidboot.mode=sd androidboot.hardware=rk30board"
FSTAB = """/dev/block/platform/30000000.rksdmmc/by-name/system /system ext4 ro,noatime wait
/dev/block/platform/30000000.rksdmmc/by-name/cache /cache ext4 noatime wait
/dev/block/platform/30000000.rksdmmc/by-name/metadata /metadata ext4 noatime wait,check
/dev/block/platform/30000000.rksdmmc/by-name/userdata /data ext4 noatime wait,check
/dev/block/platform/30000000.rksdmmc/by-name/misc /misc emmc defaults defaults
"""
CONFIG = "\n".join("CONFIG_" + key + "=y" for key in
                   ("MMC", "MMC_BLOCK", "MMC_DW", "MMC_DW_PLTFM", "MMC_DW_ROCKCHIP", "HOTPLUG_CPU", "EFI_PARTITION"))
CONFIG += "\n# CONFIG_RK_NAND is not set\n# CONFIG_MTD is not set\n# CONFIG_BT is not set\n"


def cell(value):
    return struct.pack(">I", value)


def tree(cmdline=CMDLINE, sd_address=0x30000000, emmc_status="disabled", nand_status="disabled"):
    def controller(name, address, status, compatible):
        compatible_bytes = compatible.encode() + b"\0"
        if compatible == "rockchip,rk322x-sdmmc":
            compatible_bytes = b"rockchip,rk_mmc\0" + compatible_bytes
        props = [("compatible", compatible_bytes),
                 ("reg", cell(address) + cell(0x10000)),
                 ("status", status.encode() + b"\0")]
        if name == "rksdmmc@30000000":
            props.append(("supports-sd", b""))
        return (name, props, [])
    return ("", [("#address-cells", cell(1)), ("#size-cells", cell(1)),
                 ("compatible", b"rockchip,rk3229\0")], [
        ("chosen", [("bootargs", cmdline.encode() + b"\0")], []),
        controller("rksdmmc@30000000", sd_address, "okay", "rockchip,rk322x-sdmmc"),
        controller("rksdmmc@30020000", 0x30020000, emmc_status, "rockchip,rk322x-sdmmc"),
        controller("nandc@30030000", 0x30030000, nand_status, "rockchip,rk-nandc"),
        ("wireless-bluetooth", [("compatible", b"bluetooth-platdata\0"),
                                ("status", b"disabled\0")], []),
    ])


def fdt(root):
    """Emit a minimal FDT fixture following the wire format, independent of dtc."""
    strings = bytearray()
    offsets = {}
    def name_offset(name):
        if name not in offsets:
            offsets[name] = len(strings)
            strings.extend(name.encode() + b"\0")
        return offsets[name]
    def padded(data):
        return data + b"\0" * (-len(data) % 4)
    def encode(node):
        name, props, children = node
        result = cell(1) + padded(name.encode() + b"\0")
        for key, value in props:
            result += cell(3) + cell(len(value)) + cell(name_offset(key)) + padded(value)
        for child in children:
            result += encode(child)
        return result + cell(2)
    structure = encode(root) + cell(9)
    reserve = b"\0" * 16
    off_struct = 40 + len(reserve)
    off_strings = off_struct + len(structure)
    header = struct.pack(">10I", 0xD00DFEED, off_strings + len(strings), off_struct,
                         off_strings, 40, 17, 16, 0, len(strings), len(structure))
    return header + reserve + structure + strings


class SdBootInputChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.paths = {name: self.directory / name for name in ("fstab", "dtb", "config", "cmdline")}
        self.paths["fstab"].write_text(FSTAB)
        self.paths["dtb"].write_bytes(fdt(tree()))
        self.paths["config"].write_text(CONFIG)
        self.paths["cmdline"].write_text(CMDLINE + "\n")

    def inspect(self):
        return AUDIT.inspect(**self.paths)

    def blocked(self, check):
        report = self.inspect()
        self.assertEqual(report["status"], "blocked", report)
        failures = [item for item in report["checks"] if item["status"] == "blocked"]
        self.assertIn(check, [item["check"] for item in failures], report)
        return report

    def test_consistent_inputs_are_read_only_and_do_not_approve_boot(self):
        before = {name: (path.read_bytes(), path.stat().st_mtime_ns) for name, path in self.paths.items()}
        report = self.inspect()
        self.assertEqual(report["status"], "inputs_only", report)
        self.assertEqual(report["profile"], "rk3229-sdk-sd-reference-v1")
        self.assertEqual(report["rom_build_validation"], "not_performed")
        self.assertEqual(report["hardware_validation"], "not_performed")
        self.assertTrue(any("internal storage" in limit for limit in report["limits"]))
        for name, path in self.paths.items():
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before[name])
            self.assertEqual(report["inputs"][name]["sha256"], hashlib.sha256(before[name][0]).hexdigest())
        self.assertEqual(sorted(p.name for p in self.directory.iterdir()), sorted(self.paths))

    def test_cli_runs_from_another_directory_and_returns_structured_status(self):
        args = [sys.executable, str(SCRIPT), "--json"]
        for name, path in self.paths.items():
            args += ["--" + name, str(path)]
        result = subprocess.run(args, capture_output=True, text=True, cwd=self.directory, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "inputs_only")
        self.paths["cmdline"].write_text(CMDLINE + " androidboot.mode=emmc")
        result = subprocess.run(args, capture_output=True, text=True, cwd=self.directory, timeout=5)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "blocked")

    def test_upstream_fstab_controller_and_internal_data_are_rejected(self):
        for controller in ("ff500000.rksdmmc", "30020000.rksdmmc"):
            with self.subTest(controller=controller):
                self.paths["fstab"].write_text(FSTAB.replace("30000000.rksdmmc", controller))
                self.blocked("fstab")

    def test_matching_node_name_cannot_hide_wrong_reg_address(self):
        self.paths["dtb"].write_bytes(fdt(tree(sd_address=0xFF500000)))
        self.blocked("dtb")

    def test_enabled_internal_storage_nodes_are_rejected(self):
        for changes in ({"emmc_status": "okay"}, {"nand_status": "okay"}):
            with self.subTest(changes=changes):
                self.paths["dtb"].write_bytes(fdt(tree(**changes)))
                self.blocked("dtb")

    def test_missing_or_disabled_sd_and_missing_internal_nodes_are_rejected(self):
        for which in range(1, 4):
            sample = tree()
            sample[2].pop(which)
            with self.subTest(missing=which):
                self.paths["dtb"].write_bytes(fdt(sample))
                self.blocked("dtb")
        sample = tree()
        sample[2][1][1][2] = ("status", b"disabled\0")
        self.paths["dtb"].write_bytes(fdt(sample))
        self.blocked("dtb")

    def test_missing_dtb_bootargs_and_stale_dtb_selectors_are_rejected(self):
        sample = tree()
        sample[2].pop(0)
        self.paths["dtb"].write_bytes(fdt(sample))
        self.blocked("dtb")
        self.paths["dtb"].write_bytes(fdt(tree(cmdline=CMDLINE.replace("androidboot.mode=sd", "androidboot.mode=emmc"))))
        self.blocked("dtb")

    def test_cmdline_and_chosen_must_contain_the_same_contract(self):
        self.paths["cmdline"].write_text(CMDLINE + " console=ttyFIQ0")
        self.blocked("dtb_cmdline")
        self.paths["dtb"].write_bytes(fdt(tree(cmdline=CMDLINE + " console=ttyFIQ0")))
        self.assertEqual(self.inspect()["status"], "inputs_only")

    def test_duplicate_conflicting_or_identical_command_line_selectors_are_rejected(self):
        for token in ("androidboot.mode=emmc", "androidboot.mode=sd", "storagemedia=sd"):
            with self.subTest(token=token):
                self.paths["cmdline"].write_text(CMDLINE + " " + token)
                self.blocked("cmdline")

    def test_substring_tricks_missing_selectors_and_unknown_tokens_are_rejected(self):
        invalid = (
            CMDLINE.replace("storagemedia=sd", "storagemedia=sdcard"),
            CMDLINE.replace("androidboot.mode=sd", "xandroidboot.mode=sd"),
            CMDLINE.replace("androidboot.mode=sd", "androidboot.mode=sdextra"),
            CMDLINE.replace("androidboot.hardware=rk30board", ""),
            CMDLINE + " root=/dev/mmcblk0p7",
            CMDLINE + " mtdparts=rk29xxnand:-(system)",
            CMDLINE + " init=/system/bin/sh",
            CMDLINE + " androidboot.selinux=permissive",
            CMDLINE + " quiet",
        )
        for line in invalid:
            with self.subTest(line=line):
                self.paths["cmdline"].write_text(line)
                self.blocked("cmdline")

    def test_active_nand_mtd_bluetooth_and_modular_mmc_are_rejected(self):
        for original, replacement in (("# CONFIG_RK_NAND is not set", "CONFIG_RK_NAND=y"),
                                      ("# CONFIG_MTD is not set", "CONFIG_MTD=y"),
                                      ("# CONFIG_BT is not set", "CONFIG_BT=m"),
                                      ("CONFIG_MMC_BLOCK=y", "CONFIG_MMC_BLOCK=m"),
                                      ("CONFIG_HOTPLUG_CPU=y", "# CONFIG_HOTPLUG_CPU is not set")):
            with self.subTest(replacement=replacement):
                self.paths["config"].write_text(CONFIG.replace(original, replacement))
                self.blocked("config")

    def test_real_legacy_kconfig_symbols_may_contain_lowercase_letters(self):
        # Names emitted by ARM 3.10 Kconfig, not malformed input.
        self.paths["config"].write_text(CONFIG + "CONFIG_CPU_32v6K=y\nCONFIG_VFPv3=y\n"
                                        "# CONFIG_BATTERY_BQ27x00 is not set\n")
        self.assertEqual(self.inspect()["status"], "inputs_only")
        self.paths["config"].write_text(CONFIG + "CONFIG_CPU_32v6K=y\nCONFIG_CPU_32v6K=y\n")
        self.blocked("config")

    def test_missing_or_duplicate_config_values_are_rejected(self):
        for text in (CONFIG.replace("# CONFIG_BT is not set\n", ""),
                     CONFIG + "CONFIG_BT=y\n", CONFIG + "CONFIG_MMC=y\n"):
            with self.subTest(config=text):
                self.paths["config"].write_text(text)
                self.blocked("config")

    def test_non_ascii_and_control_bytes_are_rejected_in_text_inputs(self):
        for name, original in (("cmdline", CMDLINE), ("config", CONFIG)):
            for tail in (b"\0", b"\xff", "\u00a0".encode()):
                with self.subTest(name=name, tail=tail):
                    self.paths[name].write_bytes(original.encode() + tail)
                    self.blocked(name)
            self.paths[name].write_text(original)

    def test_truncated_wrong_version_overlapping_and_oversized_fdt_are_rejected(self):
        original = fdt(tree())
        invalid = [b"", original[:39], original[:-1], original + b"\0"]
        for index, value in ((0, 0), (5, 16), (2, 41), (3, 40), (4, 8), (9, 0xFFFFFFFC)):
            changed = bytearray(original)
            struct.pack_into(">I", changed, index * 4, value)
            invalid.append(bytes(changed))
        for data in invalid:
            with self.subTest(header=data[:40]):
                self.paths["dtb"].write_bytes(data)
                self.blocked("dtb")

    def test_duplicate_nodes_and_properties_are_rejected(self):
        samples = [tree(), tree()]
        samples[0][2].append(samples[0][2][1])
        samples[1][2][1][1].append(("status", b"okay\0"))
        for sample in samples:
            with self.subTest(sample=sample):
                self.paths["dtb"].write_bytes(fdt(sample))
                self.blocked("dtb")

    def test_wrong_soc_and_extra_enabled_storage_controller_are_rejected(self):
        sample = tree()
        sample[1][-1] = ("compatible", b"rockchip,rk3288\0")
        self.paths["dtb"].write_bytes(fdt(sample))
        self.blocked("dtb")
        sample = tree()
        sample[2].append(("nandc@40000000", [("compatible", b"rockchip,rk-nandc\0"),
                                           ("reg", cell(0x40000000) + cell(0x10000)),
                                           ("status", b"okay\0")], []))
        self.paths["dtb"].write_bytes(fdt(sample))
        self.blocked("dtb")

    def test_sd_capabilities_must_exclude_emmc_and_explicitly_enable_sd(self):
        samples = [tree(), tree(), tree()]
        samples[0][2][1][1].append(("supports-emmc", b""))
        samples[1][2][1][1].pop()
        samples[2][2][1][1][-1] = ("supports-sd", cell(1))
        for sample in samples:
            with self.subTest(capabilities=sample[2][1][1]):
                self.paths["dtb"].write_bytes(fdt(sample))
                self.blocked("dtb")

    def test_enabled_sdio_cannot_declare_sd_or_emmc_capabilities(self):
        props = [("compatible", b"rockchip,rk_mmc\0rockchip,rk322x-sdmmc\0"),
                 ("reg", cell(0x30010000) + cell(0x10000)),
                 ("status", b"okay\0"), ("supports-sdio", b"")]
        sample = tree()
        sample[2].append(("rksdmmc@30010000", list(props), []))
        self.paths["dtb"].write_bytes(fdt(sample))
        self.assertEqual(self.inspect()["status"], "inputs_only")
        for change in ([("supports-emmc", b"")], [("supports-sd", b"")], []):
            changed = tree()
            capabilities = list(props) + change if change else props[:-1]
            changed[2].append(("rksdmmc@30010000", capabilities, []))
            with self.subTest(capabilities=capabilities):
                self.paths["dtb"].write_bytes(fdt(changed))
                self.blocked("dtb")
        sample[2][-1][1][2] = ("status", b"disabled\0")
        sample[2][-1][1].append(("supports-emmc", b""))
        self.paths["dtb"].write_bytes(fdt(sample))
        self.assertEqual(self.inspect()["status"], "inputs_only")

    def test_mmc_nodes_require_driver_binding_and_controller_type_compatibles(self):
        for which in (1, 2):
            for compatible in (b"rockchip,rk322x-sdmmc\0", b"rockchip,rk_mmc\0"):
                sample = tree()
                sample[2][which][1][0] = ("compatible", compatible)
                with self.subTest(node=which, compatible=compatible):
                    self.paths["dtb"].write_bytes(fdt(sample))
                    self.blocked("dtb")
        for compatible in (b"rockchip,rk322x-sdmmc\0", b"rockchip,rk_mmc\0"):
            sample = tree()
            sample[2].append(("rksdmmc@30010000", [("compatible", compatible),
                                ("reg", cell(0x30010000) + cell(0x10000)),
                                ("status", b"okay\0"), ("supports-sdio", b"")], []))
            self.paths["dtb"].write_bytes(fdt(sample))
            self.blocked("dtb")

    def test_enabled_generic_platform_mmc_is_rejected_but_disabled_node_is_allowed(self):
        for status in (b"okay\0", None):
            sample = tree()
            props = [("compatible", b"snps,dw-mshc\0"),
                     ("reg", cell(0x40000000) + cell(0x10000))]
            if status is not None:
                props.append(("status", status))
            sample[2].append(("mmc@40000000", props, []))
            with self.subTest(status=status):
                self.paths["dtb"].write_bytes(fdt(sample))
                self.blocked("dtb")
        sample[2][-1][1].append(("status", b"disabled\0"))
        self.paths["dtb"].write_bytes(fdt(sample))
        self.assertEqual(self.inspect()["status"], "inputs_only")
        sample = tree()
        sample[2][1][1][0] = ("compatible", b"rockchip,rk_mmc\0rockchip,rk322x-sdmmc\0snps,dw-mshc\0")
        self.paths["dtb"].write_bytes(fdt(sample))
        self.blocked("dtb")

    def test_bluetooth_platform_node_must_exist_and_be_explicitly_disabled(self):
        samples = [tree(), tree()]
        samples[0][2][-1][1][-1] = ("status", b"okay\0")
        samples[1][2].pop()
        for sample in samples:
            with self.subTest(children=sample[2]):
                self.paths["dtb"].write_bytes(fdt(sample))
                self.blocked("dtb")

    def test_unbalanced_or_unterminated_structure_is_rejected(self):
        original = fdt(tree())
        off_struct = struct.unpack_from(">I", original, 8)[0]
        size_struct = struct.unpack_from(">I", original, 36)[0]
        for offset, token in ((off_struct, 2), (off_struct + size_struct - 4, 4)):
            changed = bytearray(original)
            struct.pack_into(">I", changed, offset, token)
            self.paths["dtb"].write_bytes(changed)
            self.blocked("dtb")

    def test_missing_symlink_or_fifo_inputs_are_not_opened_as_devices(self):
        original = self.paths["dtb"]
        for replacement in (self.directory / "missing", self.directory):
            with self.subTest(path=replacement):
                self.paths["dtb"] = replacement
                self.blocked("input:dtb")
        linked = self.directory / "linked"
        linked.symlink_to(original)
        self.paths["dtb"] = linked
        self.blocked("input:dtb")
        if hasattr(os, "mkfifo"):
            fifo = self.directory / "fifo"
            os.mkfifo(fifo)
            self.paths["dtb"] = fifo
            self.blocked("input:dtb")
        self.paths["dtb"] = Path("/dev/null")
        self.blocked("input:dtb")


if __name__ == "__main__":
    unittest.main()
