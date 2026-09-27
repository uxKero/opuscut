"""Cut out images generated on a flat chroma green background and crop them to their content.

  python key_green.py char_*.png --out assets/art

Writes RGBA PNGs with the green removed and green spill pulled out of the edges.
"""
import argparse
import glob
import os

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--low", type=float, default=25)
    ap.add_argument("--high", type=float, default=110)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for path in [p for pattern in args.files for p in (glob.glob(pattern) or [pattern])]:
        a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        spill = g - np.maximum(r, b)
        alpha = 1 - np.clip((spill - args.low) / (args.high - args.low), 0, 1)
        g = np.minimum(g, np.maximum(r, b) + 6)
        im = Image.fromarray(np.dstack([r, g, b, alpha * 255]).clip(0, 255).astype(np.uint8), "RGBA")
        im = im.crop(im.getbbox())
        target = os.path.join(args.out, os.path.splitext(os.path.basename(path))[0] + ".png")
        im.save(target)
        print(f"{target}: {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    main()
