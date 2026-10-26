#!/usr/bin/env python3
"""Inspect one RK322x microSD-test fstab without mounting or writing anything.

This narrow static profile is derived from the community Android 7.1.2 SD
fstab. Passing it validates these entries only, never a boot image or device.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


MAX_INPUT_BYTES = 1024 * 1024
EXTERNAL_CONTROLLER = "ff500000.rksdmmc"
PROFILES = {
    "community-rk322x": EXTERNAL_CONTROLLER,
    "rk3229-sdk-sd-reference": "30000000.rksdmmc",
}
SOURCE_PROFILE = {
    "repository": "D042888-2/android_device_rockchip_rk322x",
    "revision": "f33a129bfab6d9cc87184ee3bf032224801fa446",
    "file": "fstab.rk30board.bootmode.sd",
}
REQUIRED = {
    "/system": ("system", "ext4"),
    "/cache": ("cache", "ext4"),
    "/metadata": ("metadata", "ext4"),
    "/data": ("userdata", "ext4"),
    "/misc": ("misc", "emmc"),
}
USB_SOURCES = {
    "/devices/ff580000.usb*", "/devices/ff5c0000.usb*",
    "/devices/ff5d0000.usb*", "/devices/usb*",
}
MOUNT_FLAGS = {
    "defaults", "ro", "rw", "noatime", "nodiratime", "nosuid", "nodev",
    "noauto_da_alloc", "discard", "barrier=0", "barrier=1",
    "errors=panic", "errors=remount-ro",
}
FS_FLAGS = {"defaults", "wait", "check", "resize", "verify", "encryptable=/metadata/key_file"}
LIMITS = (
    "This is one community RK322x SD fstab profile, not universal Rockchip storage identification.",
    "The selected controller belongs to a source reference, not confirmed on this unit.",
    "No /dev nodes are opened or resolved; runtime device links and partition contents are not checked.",
    "No init/recovery/update scripts, boot-mode selection, bootloader, kernel, DTB or HALs are audited.",
    "Passing this file check does not prove that internal storage will remain unchanged during boot.",
    "No ROM is built, no image is mounted or written, and physical boot remains unvalidated.",
)


def read_regular_file(path):
    """Reject special files/symlinks before opening and bound the regular read."""
    path = Path(os.path.abspath(os.path.expanduser(str(path))))
    if path == Path("/dev") or Path("/dev") in path.parents:
        raise ValueError("Device paths are not accepted as fstab inputs")
    for component in reversed((path,) + tuple(path.parents)):
        if component.is_symlink():
            raise ValueError("Symlink inputs or path components are not accepted")
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("Expected a regular fstab file; special files are not read")
    if before.st_size > MAX_INPUT_BYTES:
        raise ValueError("Input exceeds the 1 MiB size limit")
    # O_NONBLOCK prevents a replaced FIFO from blocking between lstat/open.
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode)
                or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
            raise ValueError("Input changed during inspection or is not a regular file")
        data = stream.read(MAX_INPUT_BYTES + 1)
        after = os.fstat(stream.fileno())
        if len(data) > MAX_INPUT_BYTES:
            raise ValueError("Input exceeds the 1 MiB size limit")
        if (opened.st_size, opened.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("Input changed during inspection")
    return path, data


def inspect(path, profile="community-rk322x"):
    if profile not in PROFILES:
        raise ValueError("Unknown SD fstab reference profile: " + str(profile))
    controller = PROFILES[profile]
    sd_by_name = "/dev/block/platform/" + controller + "/by-name/"
    report = {
        "schema_version": 1,
        "profile": profile + " / sd-fstab-static-v1",
        "source_profile": dict(SOURCE_PROFILE),
        "external_controller": controller,
        "input": {"path": str(Path(path).expanduser().absolute()),
                  "size_bytes": None, "sha256": None},
        "status": "blocked",
        "checks": [],
        "entries": [],
        "limits": list(LIMITS),
        "rom_build_validation": "not_performed",
        "hardware_validation": "not_performed",
    }
    if profile == "rk3229-sdk-sd-reference":
        report["source_profile"]["adaptation"] = {
            "patch": "rom/sdcard/patches/0004-rk3229-sdk-sd-controller.patch",
            "kernel_revision": "6c04d006ae881944d32c19e68b992d0bd5ab4fde",
            "kernel_source": "arch/arm/boot/dts/rk322x.dtsi",
        }

    def check(name, ok, message, line=None):
        item = {"check": name, "status": "pass" if ok else "blocked", "message": message}
        if line is not None:
            item["line"] = line
        report["checks"].append(item)

    try:
        actual, data = read_regular_file(path)
        report["input"] = {"path": str(actual), "size_bytes": len(data),
                           "sha256": hashlib.sha256(data).hexdigest()}
        text = data.decode("utf-8")
        if any(ord(char) < 32 and char not in "\t\r\n" for char in text):
            raise ValueError("Unexpected control character in fstab")
        check("input_file", True, "Bounded regular UTF-8 file read; no device path opened")
    except (OSError, ValueError, RuntimeError) as error:
        check("input_file", False, str(error))
        return report

    counts = {mount: 0 for mount in REQUIRED}
    optional_sources = set()
    for number, raw in enumerate(text.split("\n"), 1):
        content = raw.partition("#")[0]
        if not content.isascii():
            check("entry", False, "Non-comment fstab fields must use ASCII syntax", number)
            continue
        content = content.strip()
        if not content:
            continue
        fields = content.split()
        if len(fields) != 5:
            check("entry", False, "Expected exactly five Android fstab columns", number)
            continue
        source, mount, kind, mount_options, fs_options = fields
        mount_flags = mount_options.split(",")
        fs_flags = fs_options.split(",")
        report["entries"].append({
            "line": number, "source": source, "mount_point": mount,
            "type": kind, "mount_flags": mount_flags, "fs_mgr_flags": fs_flags,
        })
        errors = []
        if len(set(mount_flags)) != len(mount_flags) or len(set(fs_flags)) != len(fs_flags):
            errors.append("Duplicate flags are not accepted")
        if "ro" in mount_flags and "rw" in mount_flags:
            errors.append("Conflicting ro/rw mount flags")
        if mount in REQUIRED:
            counts[mount] += 1
            partition, expected_kind = REQUIRED[mount]
            if source != sd_by_name + partition:
                errors.append("Expected the reference SD source for " + mount)
            if kind != expected_kind:
                errors.append("Expected " + expected_kind + " for " + mount)
            if mount == "/misc":
                if mount_flags != ["defaults"] or fs_flags != ["defaults"]:
                    errors.append("The misc entry must use defaults/defaults")
            else:
                if not set(mount_flags).issubset(MOUNT_FLAGS) or not set(fs_flags).issubset(FS_FLAGS):
                    errors.append("Unrecognized mount or fs_mgr flags for this narrow profile")
                if mount == "/system" and ("ro" not in mount_flags or "rw" in mount_flags):
                    errors.append("The system partition must be mounted ro")
        elif source in USB_SOURCES:
            if (mount != "auto" or kind != "vfat" or mount_flags != ["defaults"]
                    or fs_flags != ["voldmanaged=usb:auto"]):
                errors.append("USB entries must use auto/vfat/defaults/voldmanaged=usb:auto")
            if source in optional_sources:
                errors.append("Duplicate optional source")
            optional_sources.add(source)
        elif source == "/dev/block/zram0":
            size = fs_options.removeprefix("zramsize=")
            if (mount != "none" or kind != "swap" or mount_flags != ["defaults"]
                    or not fs_options.startswith("zramsize=") or len(size) > 10
                    or not size.isascii() or not size.isdecimal()
                    or not 0 < int(size) <= 2 ** 32):
                errors.append("Expected the bounded zram swap entry")
            if source in optional_sources:
                errors.append("Duplicate optional source")
            optional_sources.add(source)
        else:
            if controller in source and any(flag.startswith("voldmanaged=") for flag in fs_flags):
                errors.append("Do not expose the boot SD controller as removable/formattable storage")
            else:
                errors.append("Source or mount point is outside the explicit SD/USB/zram profile")
        check("entry", not errors, "; ".join(errors) if errors else "Entry matches the static SD profile", number)

    for mount, count in counts.items():
        check("required:" + mount, count == 1,
              "Exactly one entry found" if count == 1 else "Expected exactly one entry; found " + str(count))
    if all(item["status"] == "pass" for item in report["checks"]):
        report["status"] = "fstab_only"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fstab", type=Path, help="Explicit regular fstab file; no device is accessed")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="community-rk322x",
                        help="Explicit source reference, never automatic hardware detection")
    parser.add_argument("--json", action="store_true", help="Print the structured static-inspection report")
    args = parser.parse_args(argv)
    report = inspect(args.fstab, profile=args.profile)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("RK322x SD fstab static inspection — READ ONLY")
        for item in report["checks"]:
            location = " line " + str(item["line"]) if "line" in item else ""
            print(item["status"].upper() + location + ": " + item["message"])
        print("RESULT:", report["status"], "— boot image and hardware are not validated")
        for limit in report["limits"]:
            print("LIMIT:", limit)
    return 0 if report["status"] == "fstab_only" else 2


if __name__ == "__main__":
    sys.exit(main())
