#!/usr/bin/env python3
"""Use the supplied Vortex video to make a small, native Android bootanimation.zip.

Needs ffmpeg and Pillow. 720p/12fps/128-colour default; the source plays once
and the last frame loops until Android completes boot. Does not invent logo.
Use --official to require the approved 4-second MP4 and its 48 output frames.
"""
import argparse, hashlib, io, os, subprocess, tempfile, zipfile
from pathlib import Path
from PIL import Image

OFFICIAL_VIDEO_SHA256 = "627b735c3709eff96f9d0bf69c38470a27f1d8ed095c82f6799c97c238ac0d9d"


def _validate_official_frames(frames):
    if len(frames) != 48:
        raise ValueError("Official boot animation requires exactly 48 frames at 12 fps")
    for frame in frames:
        with Image.open(frame) as image:
            if image.size != (1280, 720):
                raise ValueError("Official boot animation frames must be 1280x720")


def build(video, destination, fps=12, colors=128, official=False):
    video=Path(video);destination=Path(destination)
    if not video.is_file():raise FileNotFoundError(video)
    if destination.resolve() == video.resolve():
        raise ValueError("Output must not replace the source video")
    if not (1<=fps<=24 and 2<=colors<=256):raise ValueError("fps/colors out of range")
    if official:
        if fps != 12:
            raise ValueError("Official boot animation requires 12 fps")
        digest = hashlib.sha256()
        with video.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != OFFICIAL_VIDEO_SHA256:
            raise ValueError("Official video SHA-256 mismatch; original MP4 required")
    with tempfile.TemporaryDirectory() as temp:
        subprocess.run(["ffmpeg","-nostdin","-y","-v","error","-i",str(video),
            "-vf",f"fps={fps},scale=1280:720","-c:v","png",
            str(Path(temp)/"%04d.png")],check=True)
        frames=sorted(Path(temp).glob("*.png"))
        if not frames:raise RuntimeError("No video frames")
        if official:
            _validate_official_frames(frames)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".vortex-boot-", suffix=".zip",
                                         dir=destination.parent, delete=False) as staging:
            staged = Path(staging.name)
        try:
            with zipfile.ZipFile(staged,"w",compression=zipfile.ZIP_STORED) as output:
                output.writestr("desc.txt",f"1280 720 {fps}\np 1 0 part0\np 0 0 part1\n")
                last=None
                for i,f in enumerate(frames):
                    with Image.open(f) as source:
                        im=source.convert("RGB").quantize(colors=colors,
                            method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
                    buf=io.BytesIO();im.save(buf,format="PNG",optimize=True)
                    last=buf.getvalue()
                    output.writestr(f"part0/{i:04d}.png",last)
                output.writestr("part1/0000.png",last)
            os.replace(staged, destination)
        finally:
            staged.unlink(missing_ok=True)
    return destination.stat().st_size

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("video",type=Path)
    p.add_argument("--out",type=Path,default=Path("assets/bootanimation.zip"))
    p.add_argument("--fps",type=int,default=12)
    p.add_argument("--colors",type=int,default=128)
    p.add_argument("--official",action="store_true",
        help="require the approved MP4 SHA-256, 12 fps and 48 frames at 1280x720")
    args=p.parse_args()
    size=build(args.video,args.out,args.fps,args.colors,official=args.official)
    print(f"{args.out} ({size/1048576:.2f} MiB)")
