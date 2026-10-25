#!/usr/bin/env python3
"""Read-only prerequisite checks for the documented RK322x reference profile.

No source checkout, BSP script, build, device access or firmware write is run.
Passing these checks does not establish a complete or board-compatible BSP.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET


REFERENCE_FILES = (
    ".repo/manifest.xml",
    "build/envsetup.sh",
    "build/core/main.mk",
    "build/core/version_defaults.mk",
    "device/rockchip/rk322x/AndroidProducts.mk",
    "device/rockchip/rk322x/BoardConfig.mk",
    "device/rockchip/rk322x/rk322x_box.mk",
    "device/rockchip/common/BoardConfig.mk",
    "device/rockchip/common/tv/tv_base.mk",
    "vendor/rockchip/rk322x/BoardConfigVendor.mk",
    "kernel/Makefile",
    "kernel/arch/arm/boot/Image",
)
LIMITS = (
    "This is the documented community rk322x_box file-layout profile, not a universal Rockchip BSP validator.",
    "File presence, version strings and hashes do not prove source rights, a complete dependency graph or reproducibility.",
    "A manifest lock is checked for explicit project commit IDs, not repository availability or correspondence to this checkout.",
    "No BSP scripts, builds, firmware commands or hardware probes are executed.",
    "R329Q_V8.0 compatibility and physical boot remain unvalidated, even when the preflight exits 0.",
)


def assignment(text, name):
    values = re.findall(r"^\s*" + re.escape(name) + r"\s*:?=\s*([^#\n]+)", text, re.MULTILINE)
    return [value.strip() for value in values]


def inspect(root, manifest_lock=None):
    root = Path(root).expanduser().resolve()
    report = {
        "schema_version": 1,
        "profile": "community-rk322x_box / aosp-7.1.2_r6 reference layout",
        "bsp_root": str(root),
        "status": "blocked",
        "checks": [],
        "inventory": [],
        "limits": list(LIMITS),
        "rom_build_validation": "not_performed",
        "hardware_validation": "not_performed",
    }

    def check(name, ok, message):
        report["checks"].append({"check": name, "status": "pass" if ok else "blocked", "message": message})

    check("bsp_root", root.is_dir(), "Directory exists" if root.is_dir() else "BSP root is absent or is not a directory")
    if not root.is_dir():
        return report

    # Resolve before opening. Legitimate in-tree repo symlinks are supported;
    # symlinks escaping this explicit source root are never read.
    available = {}
    for relative in REFERENCE_FILES:
        path = root / relative
        try:
            resolved = path.resolve()
            if not resolved.is_relative_to(root):
                raise ValueError("Symlink escapes BSP root; file was not read")
            info = resolved.stat()
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("Expected a regular file")
            if info.st_size == 0:
                raise ValueError("File is empty")
            digest = hashlib.sha256()
            with resolved.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            report["inventory"].append({"path": relative, "size_bytes": info.st_size, "sha256": digest.hexdigest()})
            available[relative] = resolved
            check(relative, True, "Nonempty regular file inventoried")
        except (OSError, ValueError, RuntimeError) as error:
            message = "Missing or unreadable file" if isinstance(error, OSError) else str(error)
            check(relative, False, message)

    version_file = available.get("build/core/version_defaults.mk")
    if version_file:
        try:
            text = version_file.read_text(encoding="utf-8")
            version = assignment(text, "PLATFORM_VERSION")
            sdk = assignment(text, "PLATFORM_SDK_VERSION")
            check("android_version", version == ["7.1.2"] and sdk == ["25"],
                  "Android 7.1.2 / API 25 literal assignments found" if version == ["7.1.2"] and sdk == ["25"]
                  else "Expected unambiguous literal PLATFORM_VERSION 7.1.2 and PLATFORM_SDK_VERSION 25; inspect vendor version definitions")
        except (OSError, UnicodeError):
            check("android_version", False, "Cannot read Android version definitions as UTF-8")

    kernel_file = available.get("kernel/Makefile")
    if kernel_file:
        try:
            text = kernel_file.read_text(encoding="utf-8")
            components = [assignment(text, name) for name in ("VERSION", "PATCHLEVEL", "SUBLEVEL")]
            matching = components == [["3"], ["10"], ["104"]]
            check("kernel_reference_version", matching,
                  "Kernel 3.10.104 reference found; this does not validate its configuration or modules" if matching
                  else "Kernel version differs from, or cannot be matched to, the documented 3.10.104 reference; review BSP selection")
        except (OSError, UnicodeError):
            check("kernel_reference_version", False, "Cannot read kernel version definitions as UTF-8")

    java_home = os.environ.get("JAVA_HOME")
    java = str(Path(java_home) / "bin/java") if java_home else shutil.which("java")
    javac = str(Path(java_home) / "bin/javac") if java_home else shutil.which("javac")
    java_version = None
    javac_version = None
    if java:
        try:
            result = subprocess.run([java, "-version"], capture_output=True, text=True, timeout=10)
            match = re.search(r'(?:openjdk|java) version "([^"\n]+)"', result.stdout + result.stderr)
            if result.returncode == 0 and match:
                java_version = match.group(1)
        except (OSError, subprocess.TimeoutExpired):
            pass
    if javac:
        try:
            result = subprocess.run([javac, "-version"], capture_output=True, text=True, timeout=10)
            match = re.search(r"javac ([^\s]+)", result.stdout + result.stderr)
            if result.returncode == 0 and match:
                javac_version = match.group(1)
        except (OSError, subprocess.TimeoutExpired):
            pass
    jdk8 = bool(java_version and javac_version and java_version.startswith("1.8.") and javac_version.startswith("1.8."))
    check("jdk8", jdk8,
          "Java and javac 8 detected" if jdk8
          else "Select a working JDK 8 using JAVA_HOME/PATH; the APK's JDK 11 is a separate toolchain")
    report["java_version"] = java_version
    report["javac_version"] = javac_version
    # Capacity is observed only: modern AOSP storage guidance is not a proven
    # Nougat minimum, so this script invents no threshold for this legacy BSP.
    report["disk_free_bytes"] = shutil.disk_usage(root).free

    if manifest_lock is None:
        check("resolved_manifest", False,
              "Provide --manifest-lock FILE from repo manifest -r; .repo/manifest.xml alone is not a complete pinned-source inventory")
    else:
        lock_path = Path(manifest_lock).expanduser()
        try:
            if not stat.S_ISREG(lock_path.stat().st_mode):
                raise ValueError("Manifest lock is not a regular file")
            data = lock_path.read_bytes()
            document = ET.fromstring(data)
            projects = list(document.iter("project"))
            valid = (document.tag == "manifest" and bool(projects)
                     and not list(document.iter("include")) and not list(document.iter("extend-project"))
                     and all(project.get("name") and re.fullmatch(r"[0-9a-fA-F]{40}", project.get("revision", ""))
                             for project in projects))
            check("resolved_manifest", valid,
                  "Resolved manifest has explicit 40-hex commit IDs for all projects" if valid
                  else "Expected resolved manifest with named projects, explicit full commit IDs and no unresolved includes/extends")
            report["manifest_lock"] = {"path": str(lock_path.resolve()), "sha256": hashlib.sha256(data).hexdigest(),
                                       "project_count": len(projects)}
        except (OSError, ValueError, ET.ParseError):
            check("resolved_manifest", False, "Manifest lock is absent, unreadable or invalid XML")

    if all(item["status"] == "pass" for item in report["checks"]):
        report["status"] = "preflight_only"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bsp_root", help="Existing external BSP checkout; no files in it are changed")
    parser.add_argument("--manifest-lock", type=Path, help="Explicit resolved manifest file from repo manifest -r")
    parser.add_argument("--json", action="store_true", help="Print structured report instead of human-readable checks")
    args = parser.parse_args(argv)
    report = inspect(args.bsp_root, args.manifest_lock)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("AOSP/RK322x prerequisite inspection — READ ONLY")
        print("Profile:", report["profile"])
        for item in report["checks"]:
            print(item["status"].upper() + ": " + item["check"] + ": " + item["message"])
        print("Inventory:", len(report["inventory"]), "explicit files (use --json for SHA-256)")
        for limit in report["limits"]:
            print("LIMIT:", limit)
        print("RESULT:", report["status"], "— ROM build and hardware boot are NOT validated")
    return 0 if report["status"] == "preflight_only" else 2


if __name__ == "__main__":
    sys.exit(main())
