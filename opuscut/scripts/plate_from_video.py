"""Cut a plate from recorded footage: a time range, a speed and a crop, at the source's own resolution.

  python plate_from_video.py <video> --out plates/<id> --from 118 --to 126 [--speed 3.5] [--fps 30]
                             [--crop x,y,w,h] [--png] [--video-size 1920x1080]

Keeps the source's own resolution (no scaling here, so the canvas scales once) and writes near-lossless
frames plus plate.json with the native size. With --video-size it reports how much the plate will be
enlarged to cover the video frame, because enlarging footage is where most quality is lost.
"""
import argparse
import json
import os
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--from", dest="start", type=float, required=True)
    ap.add_argument("--to", dest="end", type=float, required=True)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--crop")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--video-size", default="1920x1080")
    args = ap.parse_args()
    vw, vh = (int(x) for x in args.video_size.lower().split("x"))
    ext = "png" if args.png else "jpg"
    os.makedirs(args.out, exist_ok=True)
    for f in os.listdir(args.out):
        if f.endswith((".jpg", ".png")):
            os.remove(os.path.join(args.out, f))
    frames = max(1, round((args.end - args.start) / args.speed * args.fps))
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", args.video], capture_output=True, text=True, check=True).stdout.strip().split(",")
    w, h = int(probe[0]), int(probe[1])
    chain = []
    if args.crop:
        x, y, cw, ch = args.crop.split(",")
        chain.append(f"crop={cw}:{ch}:{x}:{y}")
        w, h = int(cw), int(ch)
    chain += [f"setpts=PTS/{args.speed}", f"fps={args.fps}"]
    quality = [] if args.png else ["-q:v", "1", "-qmin", "1"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(args.start), "-t", str(args.end - args.start), "-i", args.video,
                    "-vf", ",".join(chain), "-frames:v", str(frames), *quality, "-start_number", "0",
                    os.path.join(args.out, f"%05d.{ext}")], check=True)
    made = len([f for f in os.listdir(args.out) if f.endswith("." + ext)])
    with open(os.path.join(args.out, "plate.json"), "w", encoding="utf-8") as fh:
        json.dump({"frames": made, "fps": args.fps, "ext": ext, "width": w, "height": h}, fh)
    cover = max(vw / w, vh / h)
    note = f"fills {vw}x{vh} at {cover:.2f}x"
    if cover > 1.3:
        note += ": enlarged, will look soft. Use a larger source or crop, or show it smaller than full frame"
    print(f"{args.out}: {made} frames, {made / args.fps:.2f} s at {args.fps} fps, native {w}x{h}, {note}")


if __name__ == "__main__":
    main()
