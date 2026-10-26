#!/usr/bin/env python3
"""Cross-check explicit RK3229 SDK SD reference inputs without using hardware.

This intentionally narrow profile checks file consistency only. It does not
build, mount or approve a boot image, a board configuration or an SD card.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

if __package__:
    from . import audit_sd_fstab
else:
    import audit_sd_fstab


PROFILE = "rk3229-sdk-sd-reference-v1"
FDT_MAGIC = 0xD00DFEED
MAX_NODES = 4096
MAX_DEPTH = 64
# In the pinned kernel, rk_mmc binds the Rockchip driver while rk322x-sdmmc
# selects its controller type. The generic platform driver binds dw-mshc.
ROCKCHIP_MMC_COMPATIBLES = {"rockchip,rk_mmc", "rockchip,rk322x-sdmmc"}
GENERIC_MMC_COMPATIBLE = "snps,dw-mshc"
CONFIG_REQUIRED = {
    "CONFIG_MMC": "y", "CONFIG_MMC_BLOCK": "y", "CONFIG_MMC_DW": "y",
    "CONFIG_MMC_DW_PLTFM": "y", "CONFIG_MMC_DW_ROCKCHIP": "y", "CONFIG_HOTPLUG_CPU": "y",
    "CONFIG_EFI_PARTITION": "y", "CONFIG_RK_NAND": "n",
    "CONFIG_MTD": "n", "CONFIG_BT": "n",
}
CMDLINE_REQUIRED = {
    "storagemedia": "sd", "androidboot.mode": "sd",
    "androidboot.hardware": "rk30board",
}
CMDLINE_OPTIONAL = {
    "console": "ttyFIQ0", "androidboot.console": "ttyFIQ0",
    "androidboot.selinux": "enforcing",
    "vmalloc": "496M", "psci": "enable",
}
LIMITS = (
    "This fixed SDK reference profile is not an identified R329Q_V8.0 board configuration.",
    "DTB controller addresses and fstab paths are compared as files; runtime /dev links, partition labels and contents are not verified.",
    "The command-line file is a proposed contract, not evidence of the actual bootloader or kernel command line.",
    "No bootloader, DDR/trust, kernel binary/config correspondence, Android system, ramdisk, recovery, updater, HAL or proprietary module is approved.",
    "Disabled reference storage nodes and kernel options do not prove preservation of internal storage on physical hardware.",
    "No image is mounted or written, no device is opened, no ROM is built and no physical boot is performed.",
)


def _ascii_text(data, label):
    text = data.decode("ascii")
    if any(ord(char) < 32 and char not in "\t\r\n" for char in text):
        raise ValueError("Unexpected control character in " + label)
    return text


def parse_dtb(data):
    """Read a bounded, unambiguous FDT v17 structure; never execute dtc."""
    if len(data) < 40:
        raise ValueError("Truncated FDT header")
    (magic, total, off_struct, off_strings, off_reserve, version, compatible,
     _boot_cpu, size_strings, size_struct) = struct.unpack_from(">10I", data)
    if magic != FDT_MAGIC or version != 17 or compatible not in (16, 17):
        raise ValueError("Expected an FDT v17 header")
    if total != len(data) or total > audit_sd_fstab.MAX_INPUT_BYTES:
        raise ValueError("FDT totalsize must match the bounded input exactly")
    if off_struct % 4 or off_reserve % 8:
        raise ValueError("Misaligned FDT block offset")
    regions = [(0, 40)]
    for offset, size in ((off_struct, size_struct), (off_strings, size_strings)):
        if offset < 40 or not size or offset + size > total:
            raise ValueError("FDT block is outside the input")
        regions.append((offset, offset + size))
    if off_reserve < 40 or off_reserve + 16 > total:
        raise ValueError("FDT reservation block is outside the input")
    position = off_reserve
    while True:
        if position + 16 > total:
            raise ValueError("Unterminated FDT reservation map")
        entry = struct.unpack_from(">QQ", data, position)
        position += 16
        if entry == (0, 0):
            break
    regions.append((off_reserve, position))
    regions.sort()
    if any(left[1] > right[0] for left, right in zip(regions, regions[1:])):
        raise ValueError("Overlapping FDT blocks")

    strings = data[off_strings:off_strings + size_strings]
    position, end = off_struct, off_struct + size_struct
    nodes, stack, children = {}, [], set()
    root_closed = False
    properties = 0
    while position + 4 <= end:
        token = struct.unpack_from(">I", data, position)[0]
        position += 4
        if token == 1:  # FDT_BEGIN_NODE
            zero = data.find(b"\0", position, end)
            if zero < 0:
                raise ValueError("Unterminated FDT node name")
            name = data[position:zero].decode("ascii")
            position = (zero + 4) & ~3
            if position > end:
                raise ValueError("Truncated FDT node padding")
            if not stack:
                if nodes or root_closed or name:
                    raise ValueError("FDT must contain one empty-name root")
                path = "/"
            else:
                if not re.fullmatch(r"[A-Za-z0-9,._+?@-]+", name):
                    raise ValueError("Invalid FDT node name")
                children.add(stack[-1])
                path = stack[-1].rstrip("/") + "/" + name
            if path in nodes or len(nodes) >= MAX_NODES or len(stack) >= MAX_DEPTH:
                raise ValueError("Duplicate FDT node or tree limit exceeded")
            nodes[path] = {}
            stack.append(path)
        elif token == 2:  # FDT_END_NODE
            if not stack:
                raise ValueError("Unbalanced FDT END_NODE")
            stack.pop()
            if not stack:
                root_closed = True
        elif token == 3:  # FDT_PROP
            if not stack or position + 8 > end or stack[-1] in children:
                raise ValueError("Misplaced or truncated FDT property")
            length, name_offset = struct.unpack_from(">II", data, position)
            position += 8
            if name_offset >= len(strings):
                raise ValueError("Invalid FDT property name offset")
            zero = strings.find(b"\0", name_offset)
            if zero < 0:
                raise ValueError("Unterminated FDT property name")
            name = strings[name_offset:zero].decode("ascii")
            if not re.fullmatch(r"[A-Za-z0-9,._+?#-]+", name):
                raise ValueError("Invalid FDT property name")
            if length > end - position or name in nodes[stack[-1]]:
                raise ValueError("Truncated or duplicate FDT property")
            nodes[stack[-1]][name] = data[position:position + length]
            position = (position + length + 3) & ~3
            properties += 1
            if position > end or properties > 16384:
                raise ValueError("FDT property limit or padding exceeded")
        elif token == 4:  # FDT_NOP
            continue
        elif token == 9:  # FDT_END
            if stack or not root_closed or position != end:
                raise ValueError("Unbalanced FDT tree or trailing structure data")
            return nodes
        else:
            raise ValueError("Unknown FDT structure token")
    raise ValueError("FDT END token is missing")


def _strings(value):
    if not value or not value.endswith(b"\0"):
        raise ValueError("Expected a NUL-terminated FDT string property")
    result = value[:-1].decode("ascii").split("\0")
    if any(not item or any(ord(char) < 32 or ord(char) > 126 for char in item) for item in result):
        raise ValueError("Invalid FDT string property")
    return result


def _register(nodes, path):
    parent = path.rpartition("/")[0] or "/"
    props = nodes[parent]
    address_cells = props.get("#address-cells", struct.pack(">I", 2))
    size_cells = props.get("#size-cells", struct.pack(">I", 1))
    if len(address_cells) != 4 or len(size_cells) != 4:
        raise ValueError("Invalid parent address/size cell count")
    addresses, sizes = struct.unpack(">I", address_cells)[0], struct.unpack(">I", size_cells)[0]
    if addresses not in (1, 2) or sizes not in (1, 2):
        raise ValueError("Unsupported parent address/size cell count")
    value = nodes[path].get("reg", b"")
    if len(value) != 4 * (addresses + sizes):
        raise ValueError("Expected exactly one controller reg range")
    address = int.from_bytes(value[:4 * addresses], "big")
    size = int.from_bytes(value[4 * addresses:], "big")
    if not size:
        raise ValueError("Controller reg range must have nonzero size")
    return address


def inspect_dtb(data):
    nodes = parse_dtb(data)
    if "rockchip,rk3229" not in _strings(nodes["/"].get("compatible", b"")):
        raise ValueError("DTB root does not identify the RK3229 reference SoC")
    if "status" in nodes["/"] and _strings(nodes["/"]["status"]) not in (["okay"], ["ok"]):
        raise ValueError("DTB root is not enabled")
    results = []
    expected = (
        ("/rksdmmc@30000000", 0x30000000, "okay", ROCKCHIP_MMC_COMPATIBLES),
        ("/rksdmmc@30020000", 0x30020000, "disabled", ROCKCHIP_MMC_COMPATIBLES),
        ("/nandc@30030000", 0x30030000, "disabled", {"rockchip,rk-nandc"}),
    )
    for path, address, status, compatible in expected:
        if path not in nodes:
            raise ValueError("Missing reference DTB node: " + path)
        props = nodes[path]
        actual_status = _strings(props.get("status", b""))
        compatibles = _strings(props.get("compatible", b""))
        actual_address = _register(nodes, path)
        if actual_status != [status] or not compatible.issubset(compatibles) or actual_address != address:
            raise ValueError("DTB status/compatible/reg mismatch: " + path)
        if path == "/rksdmmc@30000000":
            if props.get("supports-sd") != b"" or "supports-emmc" in props:
                raise ValueError("SD host must declare empty supports-sd and must not support eMMC")
        results.append({"path": path, "status": status, "address": hex(address),
                        "compatible": compatibles})
    # A second enabled controller with another name must not escape the fixed
    # checks above. The SDK's separate SDIO Wi-Fi host is the only other MMC
    # node allowed by this reference; this does not identify the owner's Wi-Fi.
    expected_paths = {item[0] for item in expected}
    for path, props in nodes.items():
        if "compatible" not in props:
            continue
        compatibles = _strings(props["compatible"])
        status = _strings(props.get("status", b"okay\0"))
        if GENERIC_MMC_COMPATIBLE in compatibles and status != ["disabled"]:
            raise ValueError("Enabled generic MMC controller is outside the fixed Rockchip profile: " + path)
        if path in expected_paths:
            continue
        if "bluetooth-platdata" in compatibles:
            if _strings(props.get("status", b"okay\0")) != ["disabled"]:
                raise ValueError("Bluetooth platform device must remain disabled: " + path)
            continue
        if not (ROCKCHIP_MMC_COMPATIBLES | {"rockchip,rk-nandc", GENERIC_MMC_COMPATIBLE}).intersection(compatibles):
            continue
        if status == ["disabled"]:
            continue
        if (path != "/rksdmmc@30010000" or _register(nodes, path) != 0x30010000
                or not ROCKCHIP_MMC_COMPATIBLES.issubset(compatibles)):
            raise ValueError("Unexpected enabled reference storage controller: " + path)
        if (status not in (["okay"], ["ok"]) or props.get("supports-sdio") != b""
                or "supports-emmc" in props or "supports-sd" in props):
            raise ValueError("Enabled SDIO host must support only SDIO, without SD/eMMC capabilities")
    bluetooth = nodes.get("/wireless-bluetooth", {})
    if _strings(bluetooth.get("status", b"okay\0")) != ["disabled"]:
        raise ValueError("Expected explicit disabled /wireless-bluetooth platform node")
    if "/chosen" not in nodes or "bootargs" not in nodes["/chosen"]:
        raise ValueError("Missing DTB /chosen/bootargs for the SD reference contract")
    bootargs = _strings(nodes["/chosen"]["bootargs"])
    if len(bootargs) != 1:
        raise ValueError("Expected a single DTB bootargs string")
    return {"controllers": results,
            "disabled_platform_devices": ["/wireless-bluetooth"],
            "chosen_command_line_selectors": inspect_cmdline(bootargs[0].encode("ascii"))}


def inspect_config(data):
    config = {}
    for number, raw in enumerate(_ascii_text(data, "kernel config").splitlines(), 1):
        line = raw.strip()
        unset = re.fullmatch(r"# (CONFIG_[A-Za-z0-9_]+) is not set", line)
        assigned = re.fullmatch(r"(CONFIG_[A-Za-z0-9_]+)=(.+)", line)
        if unset:
            key, value = unset[1], "n"
        elif assigned:
            key, value = assigned[1], assigned[2]
        elif not line or line.startswith("#"):
            continue
        else:
            raise ValueError("Malformed kernel config line " + str(number))
        if key in config:
            raise ValueError("Duplicate kernel config key: " + key)
        config[key] = value
    for key, expected in CONFIG_REQUIRED.items():
        if config.get(key) != expected:
            raise ValueError("Expected " + key + "=" + expected + "; missing or different value")
    return {key: config[key] for key in CONFIG_REQUIRED}


def inspect_cmdline(data):
    values = {}
    for token in _ascii_text(data, "command line").split():
        key, separator, value = token.partition("=")
        if not separator or key not in {**CMDLINE_REQUIRED, **CMDLINE_OPTIONAL}:
            raise ValueError("Command-line token is outside the explicit SD reference contract: " + token)
        if key in values:
            raise ValueError("Duplicate command-line selector: " + key)
        expected = CMDLINE_REQUIRED.get(key, CMDLINE_OPTIONAL.get(key))
        if value != expected:
            raise ValueError("Expected exact command-line token " + key + "=" + expected)
        values[key] = value
    for key, expected in CMDLINE_REQUIRED.items():
        if values.get(key) != expected:
            raise ValueError("Missing command-line selector: " + key)
    return values


def inspect(fstab, dtb, config, cmdline):
    report = {
        "schema_version": 1, "profile": PROFILE, "status": "blocked",
        "inputs": {}, "checks": [], "limits": list(LIMITS),
        "rom_build_validation": "not_performed", "hardware_validation": "not_performed",
    }

    def check(name, ok, message):
        report["checks"].append({"check": name, "status": "pass" if ok else "blocked",
                                  "message": message})

    contents = {}
    for name, path in (("fstab", fstab), ("dtb", dtb), ("config", config), ("cmdline", cmdline)):
        try:
            actual, data = audit_sd_fstab.read_regular_file(path)
            report["inputs"][name] = {"path": str(actual), "size_bytes": len(data),
                                       "sha256": hashlib.sha256(data).hexdigest()}
            contents[name] = data
            check("input:" + name, True, "Bounded regular file read; no device opened")
        except (OSError, ValueError, RuntimeError) as error:
            check("input:" + name, False, str(error))
    if len(contents) != 4:
        return report
    fstab_report = audit_sd_fstab.inspect(fstab, profile="rk3229-sdk-sd-reference")
    report["fstab_audit"] = fstab_report
    stable = fstab_report["input"]["sha256"] == report["inputs"]["fstab"]["sha256"]
    check("fstab", fstab_report["status"] == "fstab_only" and stable,
          "RK3229 SDK fstab entries match; input remained stable" if stable else "Fstab changed during inspection")
    for name, inspect_part, result_key in (("dtb", inspect_dtb, "dtb_audit"),
                                            ("config", inspect_config, "kernel_config"),
                                            ("cmdline", inspect_cmdline, "command_line_selectors")):
        try:
            report[result_key] = inspect_part(contents[name])
            check(name, True, "Matches the explicit SDK SD reference profile")
        except (UnicodeError, ValueError, struct.error) as error:
            check(name, False, str(error))
    if "dtb_audit" in report and "command_line_selectors" in report:
        same = report["dtb_audit"]["chosen_command_line_selectors"] == report["command_line_selectors"]
        check("dtb_cmdline", same, "DTB bootargs and proposed cmdline selectors match" if same
              else "DTB bootargs differ from the proposed cmdline contract")
    if all(item["status"] == "pass" for item in report["checks"]):
        report["status"] = "inputs_only"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("fstab", "dtb", "config", "cmdline"):
        parser.add_argument("--" + name, required=True, type=Path, help="Explicit regular " + name + " file")
    parser.add_argument("--json", action="store_true", help="Print the structured input inspection report")
    args = parser.parse_args(argv)
    report = inspect(args.fstab, args.dtb, args.config, args.cmdline)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("RK3229 SDK SD reference input inspection — READ ONLY")
        for item in report["checks"]:
            print(item["status"].upper() + ": " + item["check"] + ": " + item["message"])
        print("RESULT:", report["status"], "— boot image and physical hardware are not validated")
        for limit in report["limits"]:
            print("LIMIT:", limit)
    return 0 if report["status"] == "inputs_only" else 2


if __name__ == "__main__":
    sys.exit(main())
