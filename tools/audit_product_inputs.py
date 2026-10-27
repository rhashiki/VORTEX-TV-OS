#!/usr/bin/env python3
"""Audit explicit, flattened Vortex SD product inputs without building or writing.

This fixed contract checks selected names, copied-file inputs and board values.
It does not prove how lists were generated or resolve Android module dependencies.
"""
import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import stat
import sys
import xml.etree.ElementTree as ET


MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_SOURCE_BYTES = 64 * 1024 * 1024
PROFILE = "vortex-rk322x-sd-product-inputs-v1"
REQUIRED_PACKAGES = {
    "VortexHome", "PackageInstaller", "DefaultContainerService", "Settings",
    "SystemUI", "SettingsProvider", "InputDevices", "LatinIME", "DocumentsUI",
    "ExternalStorageProvider", "framework-res", "gralloc.rk30board",
    "hwcomposer.rk30board",
}
REQUIRED_DESTINATIONS = {
    "root/init.rk30board.rc", "root/fstab.rk30board.bootmode.sd",
    "root/init.zygote32.rc", "root/init.usb.rc", "root/init.usb.configfs.rc",
    "root/ueventd.rc", "system/etc/hosts", "system/etc/public.libraries.txt",
    "system/etc/permissions/android.software.webview.xml", "system/etc/fonts.xml",
    "system/etc/audio_policy.conf", "system/lib/egl/libGLES_mali.so",
    "system/lib/egl/egl.cfg",
}
FORBIDDEN_PACKAGES = (
    "launcher*", "leanback*", "tvlauncher*", "gralloc.default", "bluetooth*", "audio.a2dp.default",
    "gms*", "prebuiltgms*", "phonesky", "google*",
    "setupwizard*", "managedprovisioning", "provision", "recovery", "updater",
    "rkupdateservice", "update_engine", "uncrypt", "applypatch", "rk_store_keybox",
    "drmservice", "whtest", "factorytest", "devicetest",
)
EXPECTED_CONFIG = {
    "TARGET_PRODUCT": "vortex_rk322x_sd_box",
    "TARGET_DEVICE": "vortex_rk322x_sd_box",
    "TARGET_BOARD_PLATFORM": "rk322x",
    "TARGET_BOARD_PLATFORM_GPU": "mali400",
    "TARGET_BOARD_HARDWARE": "rk30board",
    "TARGET_ARCH": "arm",
    "TARGET_ARCH_VARIANT": "armv7-a-neon",
    "TARGET_CPU_VARIANT": "cortex-a7",
    "TARGET_BOARD_PLATFORM_PRODUCT": "box",
    "TARGET_NO_RECOVERY": "true",
    "TARGET_ROCHCHIP_RECOVERY": "false",
    "TARGET_ROCKCHIP_PCBATEST": "false",
    "RECOVERY_AUTO_USB_UPDATE": "false",
    "BUILD_WITH_DRMSERVICE": "false",
    "ENABLE_KEYBOX_PROVISION": "false",
    "BOARD_HAVE_BLUETOOTH": "false",
    "BLUETOOTH_USE_BPLUS": "false",
    "BOARD_HAVE_BLUETOOTH_BCM": "false",
    "BUILD_WITH_GOOGLE_MARKET": "false",
    "BUILD_BOX_WITH_GOOGLE_MARKET": "false",
    "BUILD_WITH_GOOGLE_MARKET_ALL": "false",
    "BUILD_WITH_GOOGLE_FRP": "false",
    "TARGET_RELEASETOOLS_EXTENSIONS": "",
    "BOARD_CONNECTIVITY_VENDOR": "",
    "BOARD_CONNECTIVITY_MODULE": "",
    "BOARD_WLAN_DEVICE": "",
    "BOARD_WPA_SUPPLICANT_PRIVATE_LIB": "",
    "BOARD_HOSTAPD_PRIVATE_LIB": "",
    "WIFI_DRIVER_FW_PATH_PARAM": "",
    "WIFI_DRIVER_FW_PATH_STA": "",
    "WIFI_DRIVER_FW_PATH_P2P": "",
    "WIFI_DRIVER_FW_PATH_AP": "",
}
LIMITS = (
    "Only the supplied flattened names, copied-file inputs and explicit board values are checked; the producer of these lists is not authenticated.",
    "Module definitions, transitive dependencies, compiler/link/install behavior and final image inventory are not resolved.",
    "Font package names and fonts.xml presence do not prove font payload availability or rendering.",
    "Resource overlays, product properties and first-boot provisioning behavior are not inspected by this list-based contract.",
    "Init semantics, SELinux/device permissions, mount/USB-vold matching, recovery/BCB error paths and internal-storage preservation are not approved.",
    "No driver, proprietary ABI, bootloader, kernel/DTB, Android/SD image or physical hardware compatibility is approved.",
    "No build or BSP script is executed; no device is opened, image mounted or data written by this auditor.",
)


def forbidden_location(path):
    return any(path == Path(prefix) or Path(prefix) in path.parents
               for prefix in ("/dev", "/proc", "/sys"))


def regular_read(path, limit, reject_directory_symlinks=False):
    """Return stable regular bytes, rejecting device/special paths before open."""
    path = Path(os.path.abspath(os.path.expanduser(str(path))))
    if forbidden_location(path):
        raise ValueError("Device/process/kernel pseudo-filesystem paths are not accepted")
    if reject_directory_symlinks:
        for part in (path,) + tuple(path.parents):
            if part.is_symlink():
                raise ValueError("List inputs cannot use symlinks or symlink directories")
    elif path.is_symlink():
        raise ValueError("Copied source files cannot themselves be symlinks")
    resolved = path.resolve(strict=True)
    if forbidden_location(resolved):
        raise ValueError("Resolved source is a device/process/kernel pseudo-filesystem path")
    before = resolved.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("Expected a regular file; special files are not opened")
    if before.st_size > limit:
        raise ValueError("File exceeds the bounded read limit of %d bytes" % limit)
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(resolved, flags)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode)
                or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
            raise ValueError("File changed before it could be inspected")
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        if len(data) > limit or (opened.st_size, opened.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("File changed during inspection or exceeds its read limit")
    return resolved, data


def list_input(path):
    resolved, data = regular_read(path, MAX_INPUT_BYTES, True)
    text = data.decode("utf-8")
    if any(ord(c) < 32 and c not in "\t\r\n" for c in text):
        raise ValueError("Unexpected control character in list input")
    if "@inherit" in text or "$(" in text or "${" in text:
        raise ValueError("Input contains unresolved inheritance or make expressions")
    return text, {"path": str(resolved), "size_bytes": len(data),
                  "sha256": hashlib.sha256(data).hexdigest()}


def relative_path(value, label):
    if (not value or not value.isascii() or value.startswith("/")
            or "\\" in value or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError(label + " must be a relative POSIX file path without dot/parent components")
    normalized = posixpath.normpath(value)
    if normalized != value:
        raise ValueError(label + " aliases must be canonical (no repeated/trailing slashes)")
    return normalized


def forbidden_copy(source, destination, data=None):
    combined = ("/" + source + "/" + destination).lower()
    source_name = posixpath.basename(source).lower()
    name = posixpath.basename(destination).lower()
    if name in ("gralloc.default.so", "gralloc.rk30board.so", "hwcomposer.rk30board.so"):
        return "Copied prebuilt HAL can shadow the required source module"
    if ("/rtkbt/" in combined or "/bluetooth/" in combined
            or any(base.endswith(".hcd") or base.startswith(("libbluetooth", "libbt-"))
                   or base == "audio.a2dp.default.so" for base in (source_name, name))):
        return "Bluetooth HAL/plugin/firmware copy is outside this profile"
    if ("com.google." in combined or "/gapps/" in combined
            or any(base in ("gmscore.apk", "prebuiltgmscore.apk", "phonesky.apk",
                            "googleservicesframework.apk", "googleloginservice.apk")
                   for base in (source_name, name))):
        return "Google feature/library copy is outside this profile"
    if "fstab" in source_name and source_name != "fstab.rk30board.bootmode.sd":
        return "Only the explicitly named SD fstab source is within this profile"
    if "fstab" in name and destination != "root/fstab.rk30board.bootmode.sd":
        return "Only the explicit SD fstab destination is within this profile"
    if ("fstab" in name or name.startswith("init.")) and any(
            marker in name for marker in (".emmc", ".nand", ".unknown", ".nvme")):
        return "Internal/fallback boot-mode input is outside this SD profile"
    if name in ("librockchip_update_jni.so", "install-recovery.sh", "recovery-from-boot.p",
                "rk_store_keybox", "drmservice", "whtest", "preinstall_cleanup.sh"):
        return "Updater/recovery/factory provisioning copy is outside this profile"
    if data is not None and destination.lower().endswith(".xml"):
        try:
            xml = ET.fromstring(data)
        except (ET.ParseError, ValueError, LookupError) as error:
            return "Copied XML could not be parsed: " + str(error)
        for element in xml.iter():
            for value in element.attrib.values():
                if ("GOOGLE_BUILD" in value or "GOOGLE_EXPERIENCE" in value
                        or "com.google." in value):
                    return "Copied XML declares Google features/libraries outside this profile"
    return None


def inspect(packages_path, copies_path, config_path, bsp_root):
    report = {"schema_version": 1, "profile": PROFILE, "status": "blocked",
              "inputs": {}, "checks": [], "packages": [], "copies": [], "config_values": {},
              "limits": list(LIMITS), "rom_build_validation": "not_performed",
              "hardware_validation": "not_performed"}

    def check(name, ok, message, entry=None):
        record = {"check": name, "status": "pass" if ok else "blocked", "message": message}
        if entry is not None:
            record["entry"] = entry
        report["checks"].append(record)

    texts = {}
    for name, path in (("packages", packages_path), ("copy_files", copies_path), ("config_values", config_path)):
        try:
            texts[name], report["inputs"][name] = list_input(path)
            check("input:" + name, True, "Bounded regular UTF-8 input; no unresolved make markers")
        except (OSError, ValueError, RuntimeError) as error:
            check("input:" + name, False, str(error))
    try:
        root = Path(bsp_root).expanduser().resolve(strict=True)
        if not root.is_dir() or forbidden_location(root):
            raise ValueError("BSP root must be an explicit source directory outside /dev, /proc and /sys")
        report["bsp_root"] = str(root)
        check("bsp_root", True, "Explicit directory used only for declared copy-source reads")
    except (OSError, ValueError, RuntimeError) as error:
        check("bsp_root", False, str(error))
        root = None
    if len(texts) != 3 or root is None:
        return report

    packages = texts["packages"].split()
    report["packages"] = packages
    syntax = all(re.fullmatch(r"[A-Za-z0-9_.+\-]+", p) for p in packages)
    check("package_syntax", bool(packages) and syntax, "Expected resolved module names only")
    missing = sorted(REQUIRED_PACKAGES - set(packages))
    check("required_packages", not missing, "Missing: " + ", ".join(missing) if missing else "All required named components selected")
    forbidden = sorted({p for p in packages if any(fnmatch.fnmatchcase(p.lower(), pattern) for pattern in FORBIDDEN_PACKAGES)})
    check("forbidden_packages", not forbidden, "Forbidden selection: " + ", ".join(forbidden) if forbidden else "No named stock launcher/BT/Google/updater/factory package selected")
    report["package_counts"] = {"entries": len(packages), "unique": len(set(packages))}

    values = {}
    for number, line in enumerate(texts["config_values"].splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)", line)
        if not match or match.group(1) in values:
            check("config_record", False, "Malformed or repeated configuration key", number)
            continue
        values[match.group(1)] = match.group(2).strip()
    report["config_values"] = values
    for key, expected in EXPECTED_CONFIG.items():
        actual = values.get(key)
        check("config:" + key, actual == expected,
              "Expected explicit %s=%r; observed %r" % (key, expected, actual))

    destinations = {}
    for number, token in enumerate(texts["copy_files"].split(), 1):
        parts = token.split(":")
        if len(parts) not in (2, 3) or (len(parts) == 3 and not re.fullmatch(r"[A-Za-z0-9_.\-]+", parts[2])):
            check("copy_record", False, "Expected SRC:DST[:owner]", number)
            continue
        source, destination = parts[:2]
        try:
            normalized_source = relative_path(source, "Source")
            normalized_destination = relative_path(destination, "Destination")
        except ValueError as error:
            check("copy_path", False, str(error), token)
            continue
        identity = (normalized_source, parts[2] if len(parts) == 3 else None)
        previous = destinations.get(normalized_destination)
        if previous is not None and previous != identity:
            check("copy_conflict", False, "Different source/owner for the same normalized destination", normalized_destination)
        else:
            destinations[normalized_destination] = identity
        reason = forbidden_copy(normalized_source, normalized_destination)
        check("copy_policy", reason is None, reason or "Copy destination is within the declared profile", token)
        record = {"source": source, "destination": destination, "owner": identity[1]}
        report["copies"].append(record)
        try:
            resolved, data = regular_read(root / normalized_source, MAX_SOURCE_BYTES)
            record.update({"resolved_source": str(resolved), "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
            content_reason = forbidden_copy(normalized_source, normalized_destination, data)
            check("copy_source", content_reason is None, content_reason or "Regular stable source bytes found and hashed", token)
        except (OSError, ValueError, RuntimeError) as error:
            check("copy_source", False, str(error), token)
    missing = sorted(REQUIRED_DESTINATIONS - set(destinations))
    check("required_copies", not missing, "Missing destinations: " + ", ".join(missing) if missing else "All required declared destinations found")
    report["copy_counts"] = {"entries": len(report["copies"]), "unique_destinations": len(destinations)}
    if all(c["status"] == "pass" for c in report["checks"]):
        report["status"] = "product_inputs_only"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", required=True, type=Path)
    parser.add_argument("--copy-files", required=True, type=Path)
    parser.add_argument("--config-values", required=True, type=Path)
    parser.add_argument("--bsp-root", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = inspect(args.packages, args.copy_files, args.config_values, args.bsp_root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print("%s: %s" % (PROFILE, report["status"]))
        for item in report["checks"]:
            if item["status"] != "pass":
                print("BLOCKED %s: %s" % (item["check"], item["message"]))
        print("Product inputs only; no build, image, driver or hardware approval.")
    return 0 if report["status"] == "product_inputs_only" else 2


if __name__ == "__main__":
    sys.exit(main())
