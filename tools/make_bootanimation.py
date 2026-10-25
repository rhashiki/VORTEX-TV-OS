#!/usr/bin/env python3
"""Generates a provisional 720p bootanimation.zip.
Official two-wave Vortex logo can be supplied with --logo; no replacement art is invented.
Requirements: Pillow and numpy. Run locally, not via GitHub Actions.
"""
from pathlib import Path
import argparse, io, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, FRAMES = 1280, 720, 24, 36
parser = argparse.ArgumentParser()
parser.add_argument("--logo", type=Path)
parser.add_argument("--out", type=Path, default=Path("assets/bootanimation.zip"))
args = parser.parse_args()
if args.logo and not args.logo.is_file():
    parser.error("Official Vortex logo file not found")
args.out.parent.mkdir(parents=True, exist_ok=True)
x = np.linspace(0, 1, W)[None, :, None]
y = np.linspace(0, 1, H)[:, None, None]
t = np.clip(.58*x + .42*y, 0, 1)
c0 = np.array([22, 7, 53], dtype=float)[None, None, :]
c1 = np.array([12, 54, 117], dtype=float)[None, None, :]
base = Image.fromarray(np.uint8(np.clip(c0*(1-t)+c1*t, 0, 255)), "RGB").convert("RGBA")
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
logo = Image.open(args.logo).convert("RGBA") if args.logo else None
if logo:
    logo.thumbnail((530, 300), Image.Resampling.LANCZOS)

def frame(alpha):
    result = base.copy()
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    if logo:
        lx, ly = (W-logo.width)//2, (H-logo.height)//2-55
        sprite = logo.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda v: int(v*alpha)))
        overlay.alpha_composite(sprite, (lx, ly))
        cy = ly + logo.height + 42
    else:
        cy = 340
    title = "VORTEX TV OS"
    bounds = draw.textbbox((0,0), title, font=font)
    draw.text(((W-(bounds[2]-bounds[0]))/2, cy), title, font=font,
              fill=(255,255,255,int(245*alpha)))
    subtitle = "INICIANDO SISTEMA"
    bounds = draw.textbbox((0,0), subtitle, font=small)
    draw.text(((W-(bounds[2]-bounds[0]))/2, cy+93), subtitle, font=small,
              fill=(202,201,237,int(190*alpha)))
    result.alpha_composite(overlay)
    buf = io.BytesIO()
    result.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()

with zipfile.ZipFile(args.out, "w", compression=zipfile.ZIP_STORED) as output:
    output.writestr("desc.txt", f"{W} {H} {FPS}\np 1 0 part0\np 0 0 part1\n")
    for n in range(FRAMES):
        output.writestr(f"part0/{n:04d}.png", frame(min(1, (n+1)/20)))
    output.writestr("part1/0000.png", frame(1))
print(f"Generated {args.out}")
