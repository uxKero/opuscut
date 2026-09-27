"""Measure voice lines so the picture can follow them: duration, speech start and end, and a per-frame mouth value.

  python voice_envelope.py voice/*.mp3 --fps 30 --out voice.json

For each file it writes {"file", "duration", "speech": [start, end], "mouth": [0..1 per frame]}.
Use the durations to size each beat (the voice sets the clock) and "mouth" to open a character's mouth.
"""
import argparse
import glob
import json
import subprocess

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default="voice.json")
    args = ap.parse_args()
    sr = 16000
    result = []
    paths = [p for pattern in args.files for p in (glob.glob(pattern) or [pattern])]
    for path in paths:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        y = np.frombuffer(raw, np.float32)
        hop = sr // args.fps
        n = max(1, len(y) // hop)
        rms = np.sqrt((y[: n * hop].reshape(n, hop) ** 2).mean(1))
        db = 20 * np.log10(rms + 1e-9)
        voiced = db > max(-45.0, db.max() - 35)
        idx = np.where(voiced)[0]
        mouth = np.clip((db + 45) / 30, 0, 1) * voiced
        mouth = np.convolve(mouth, [0.25, 0.5, 0.25], "same")
        result.append({
            "file": path,
            "duration": round(len(y) / sr, 3),
            "speech": [round(idx[0] / args.fps, 3), round((idx[-1] + 1) / args.fps, 3)] if len(idx) else [0, 0],
            "mouth": [round(float(v), 2) for v in mouth],
        })
        print(f"{path}: {len(y) / sr:.2f} s, speech {result[-1]['speech'][0]}-{result[-1]['speech'][1]} s")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"fps": args.fps, "lines": result}, fh)
    print(args.out)


if __name__ == "__main__":
    main()
