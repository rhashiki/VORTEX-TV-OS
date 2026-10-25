#!/usr/bin/env python3
"""Import only the three official JPEG masters identified in ROADMAP.md.

The original bytes are preserved, including when an input is named .png. PNG
resources are resized proportionally, without cropping, recoloring or adding a
background. This does not edit the manifest/Home or import the boot video.
Actual originals are required: repository previews and generated art are refused.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile


ASSETS = (
    {
        "name": "square",
        "sha256": "bc20b1af97cdead54e3d12f6a4b224e7cd9860c80aaeeb685430e43e55bba7d3",
        "size": (1536, 1536),
        "target": (192, 192),
        "source": "branding/source/vortex-launcher-icon-square.jpg",
        "resource": "app/src/main/res/mipmap-nodpi/ic_launcher.png",
    },
    {
        "name": "banner",
        "sha256": "fae9dca1d4da7c0f7082daeed0a67300a45e2bda663bdcdcbc9daabb089b707c",
        "size": (1536, 864),
        "target": (320, 180),
        "source": "branding/source/vortex-launcher-banner-tv.jpg",
        "resource": "app/src/main/res/drawable-nodpi/vortex_tv_banner.png",
    },
    {
        "name": "logo",
        "sha256": "0cb93dcdc414487b0095499260a069fe5ae9dbd3cafd1fb5992a0ed02f9d0920",
        "size": (1536, 646),
        "target": (480, 202),
        "source": "branding/source/vortex-logo-complete.jpg",
        "resource": "app/src/main/res/drawable-nodpi/vortex_home_logo.png",
    },
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def safe_output(root, relative):
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise ValueError("Output symlink escapes repository: " + relative)
    # Refuse even an in-tree final symlink: preserving a symlink is not importing
    # an original or a resource, and replacing one could destroy another file.
    if path.is_symlink():
        raise ValueError("Output is a symlink: " + relative)
    return path


def prepare_import(inputs, repo_root):
    """Validate every input/output and derive everything in memory before writes."""
    try:
        from PIL import Image
    except ImportError as error:
        raise ValueError("Pillow is required; install it before importing assets") from error

    root = Path(repo_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Repository root is not an existing directory: " + str(root))

    plan = []
    report = {"schema_version": 1, "status": "checked", "assets": []}
    for asset in ASSETS:
        name = asset["name"]
        source = Path(inputs[name]).expanduser()
        if not source.is_file():
            raise ValueError(name + ": original file is absent: " + str(source))
        original = source.read_bytes()
        digest = sha256(original)
        if digest != asset["sha256"]:
            raise ValueError(name + ": SHA-256 mismatch; expected " + asset["sha256"]
                             + ", received " + digest + ". Previews/substitutes are not accepted.")
        with Image.open(io.BytesIO(original)) as image:
            if image.format != "JPEG" or image.mode != "RGB" or image.size != asset["size"]:
                raise ValueError(name + ": expected RGB JPEG " + str(asset["size"]))
            image.load()
            # Pixel dimensions are rounded only for the fractional 480px logo
            # height. No crop, padding, mask, color change or invented art.
            resized = image.resize(asset["target"], Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            resized.save(buffer, format="PNG", optimize=True)
            resource = buffer.getvalue()
        item = {
            "name": name,
            "source": {"path": asset["source"], "sha256": digest,
                       "size_bytes": len(original), "dimensions": list(asset["size"])},
            "resource": {"path": asset["resource"], "sha256": sha256(resource),
                         "size_bytes": len(resource), "dimensions": list(asset["target"])},
        }
        report["assets"].append(item)
        plan.extend(((asset["source"], original), (asset["resource"], resource)))

    for relative, data in plan:
        path = safe_output(root, relative)
        if path.exists() and (not path.is_file() or path.read_bytes() != data):
            raise ValueError("Refusing to overwrite different output: " + relative)
        # Check existing parents before staging or creating any directory.
        for parent in path.parents:
            if parent == root:
                break
            if parent.exists() and not parent.is_dir():
                raise ValueError("Output parent is not a directory: " + str(parent))
    return root, plan, report


def write_import(root, plan):
    """Stage files, publish without replacement, and roll back on write errors."""
    created_files = []
    created_dirs = []
    try:
        with tempfile.TemporaryDirectory(prefix=".vortex-branding-", dir=root) as stage:
            staged = []
            for index, (relative, data) in enumerate(plan):
                destination = safe_output(root, relative)
                if destination.exists():
                    if destination.read_bytes() != data:
                        raise ValueError("Output changed while importing: " + relative)
                    continue
                temporary = Path(stage) / str(index)
                temporary.write_bytes(data)
                staged.append((relative, temporary))
            for relative, temporary in staged:
                destination = safe_output(root, relative)
                parents = []
                parent = destination.parent
                while not parent.exists():
                    parents.append(parent)
                    parent = parent.parent
                for parent in reversed(parents):
                    parent.mkdir()
                    created_dirs.append(parent)
                # Hard-link is atomic and refuses to replace an existing path.
                # Staging inside the repository keeps both on one filesystem.
                os.link(temporary, destination)
                created_files.append(destination)
    except (OSError, ValueError):
        for path in reversed(created_files):
            path.unlink()
        for path in reversed(created_dirs):
            path.rmdir()
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--square", required=True, type=Path, help="Official square JPEG (possibly named .png)")
    parser.add_argument("--banner", required=True, type=Path, help="Official 16:9 JPEG (possibly named .png)")
    parser.add_argument("--logo", required=True, type=Path, help="Official complete Home JPEG (possibly named .png)")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check-only", action="store_true", help="Verify and derive in memory without writing any file")
    args = parser.parse_args(argv)
    try:
        root, plan, report = prepare_import(
            {"square": args.square, "banner": args.banner, "logo": args.logo}, args.repo_root)
        if not args.check_only:
            write_import(root, plan)
            report["status"] = "imported"
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"schema_version": 1, "status": "blocked", "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
