#!/usr/bin/env python3
"""Use the supplied Vortex video to make a small, native Android bootanimation.zip.

Needs ffmpeg and Pillow. 720p/12fps/128-colour default; 6s plays once
and the last frame loops until Android completes boot. Does not invent logo.
"""
import argparse, io, subprocess, tempfile, zipfile
from pathlib import Path
from PIL import Image

def build(video, destination, fps=12, colors=128):
    video=Path(video);destination=Path(destination)
    if not video.is_file():raise FileNotFoundError(video)
    if not (1<=fps<=24 and 2<=colors<=256):raise ValueError("fps/colors out of range")
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        subprocess.run(["ffmpeg","-nostdin","-y","-v","error","-i",str(video),
            "-vf",f"fps={fps},scale=1280:720","-c:v","png",
            str(Path(temp)/"%04d.png")],check=True)
        frames=sorted(Path(temp).glob("*.png"))
        if not frames:raise RuntimeError("No video frames")
        with zipfile.ZipFile(destination,"w",compression=zipfile.ZIP_STORED) as output:
            output.writestr("desc.txt",f"1280 720 {fps}\np 1 0 part0\np 0 0 part1\n")
            last=None
            for i,f in enumerate(frames):
                im=Image.open(f).convert("RGB").quantize(colors=colors,
                    method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
                buf=io.BytesIO();im.save(buf,format="PNG",optimize=True)
                last=buf.getvalue()
                output.writestr(f"part0/{i:04d}.png",last)
            output.writestr("part1/0000.png",last)
    return destination.stat().st_size

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("video",type=Path)
    p.add_argument("--out",type=Path,default=Path("assets/bootanimation.zip"))
    p.add_argument("--fps",type=int,default=12)
    p.add_argument("--colors",type=int,default=128)
    args=p.parse_args()
    size=build(args.video,args.out,args.fps,args.colors)
    print(f"{args.out} ({size/1048576:.2f} MiB)")
