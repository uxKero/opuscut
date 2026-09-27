"""Check a rendered MP4: stream facts, black and frozen stretches, flashes, loudness and the audio tail.

  python qa.py out/video.mp4 [--expect-seconds 15]
"""
import argparse
import json
import re
import shutil
import subprocess
import sys

import numpy as np


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--expect-seconds", type=float)
    args = ap.parse_args()
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found on PATH")
    problems, notes = [], []

    info = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", args.video]).stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    num, den = v["avg_frame_rate"].split("/")
    fps = float(num) / float(den)
    notes.append(f"{v['width']}x{v['height']}, {fps:.2f} fps, {dur:.3f} s, {v['codec_name']} {v.get('pix_fmt')}, audio: {a['codec_name'] if a else 'none'}")
    if args.expect_seconds and abs(dur - args.expect_seconds) > 1.5 / fps:
        problems.append(f"duration {dur:.3f} s, expected {args.expect_seconds} s")
    if v.get("pix_fmt") not in ("yuv420p", "yuvj420p"):
        problems.append(f"pixel format {v.get('pix_fmt')}; most players want yuv420p")

    dec = run(["ffmpeg", "-v", "error", "-i", args.video, "-f", "null", "-"])
    if dec.stderr.strip():
        problems.append("decode errors: " + dec.stderr.strip().splitlines()[0])

    det = run(["ffmpeg", "-v", "info", "-i", args.video, "-vf", "blackdetect=d=0.1:pix_th=0.08,freezedetect=n=0.001:d=0.5", "-an", "-f", "null", "-"]).stderr
    for m in re.finditer(r"black_start:([\d.]+) black_end:([\d.]+)", det):
        problems.append(f"black from {float(m.group(1)):.2f} to {float(m.group(2)):.2f} s")
    for m in re.finditer(r"freeze_start: ([\d.]+)", det):
        notes.append(f"frozen picture from {float(m.group(1)):.2f} s: confirm it is an intended hold")

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", args.video, "-vf", "scale=64:36", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    lum = np.frombuffer(raw, np.uint8).reshape(-1, 36 * 64).mean(1) / 255
    jumps = np.where(np.abs(np.diff(lum)) > 0.2)[0]
    window = int(round(fps))
    worst = max((np.sum((jumps >= i) & (jumps < i + window)) for i in range(0, max(1, len(lum) - window), max(1, window // 4))), default=0)
    flashes = worst / 2
    if flashes > 3:
        problems.append(f"about {flashes:.0f} full-frame flashes in one second; keep it at 3 or fewer")

    if a:
        ld = run(["ffmpeg", "-v", "info", "-i", args.video, "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
        i_m = re.findall(r"I:\s+(-?[\d.]+) LUFS", ld)
        p_m = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", ld)
        if i_m:
            lufs = float(i_m[-1])
            notes.append(f"loudness {lufs:.1f} LUFS integrated" + (f", true peak {float(p_m[-1]):.1f} dBTP" if p_m else ""))
            if lufs < -20 or lufs > -9:
                problems.append(f"loudness {lufs:.1f} LUFS; social platforms sit near -14")
            if p_m and float(p_m[-1]) > -0.5:
                problems.append(f"true peak {float(p_m[-1]):.1f} dBTP; keep it under -1")
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-sseof", "-0.05", "-i", args.video, "-map", "0:a", "-ac", "1", "-f", "f32le", "-"], capture_output=True).stdout
        tail = np.frombuffer(pcm, np.float32)
        if tail.size and 20 * np.log10(np.sqrt((tail ** 2).mean()) + 1e-9) > -40:
            problems.append("sound is still playing in the last 50 ms; let it resolve before the end")

    for n in notes:
        print("  ", n)
    if problems:
        for p in problems:
            print("FAIL", p)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
