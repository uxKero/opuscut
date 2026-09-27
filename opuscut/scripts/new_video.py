"""Create a video folder from the engine.

  python new_video.py <folder> [--size 1920x1080] [--fps 30] [--bpm 120] [--beats 32] [--name video]
                       [--fonts "Titan One;Inter:400,700,800;Instrument Serif:400,400i"]
"""
import argparse
import json
import os
import re
import shutil
import urllib.parse
import urllib.request

ENGINE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read()


def google_fonts(spec, assets):
    families = []
    for part in [p.strip() for p in spec.split(";") if p.strip()]:
        name, _, weights = part.partition(":")
        fam = "family=" + urllib.parse.quote_plus(name.strip())
        if weights:
            ws = [w.strip() for w in weights.split(",") if w.strip()]
            if any(w.endswith("i") for w in ws):
                pairs = sorted((1 if w.endswith("i") else 0, int(w.rstrip("i"))) for w in ws)
                fam += ":ital,wght@" + ";".join(f"{i},{w}" for i, w in pairs)
            else:
                fam += ":wght@" + ";".join(ws)
        families.append(fam)
    css = fetch("https://fonts.googleapis.com/css2?" + "&".join(families) + "&display=block").decode("utf-8")
    out, n = [], 0
    for subset, block in re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*{[^}]*})", css):
        if subset not in ("latin", "latin-ext"):
            continue
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        family = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        weight = re.search(r"font-weight:\s*([\d ]+);", block).group(1).strip()
        style = "italic" if "font-style: italic" in block else "normal"
        fname = f"{re.sub(r'[^a-z0-9]+', '-', family.lower())}-{weight.replace(' ', '-')}{'-italic' if style == 'italic' else ''}-{subset}.woff2"
        with open(os.path.join(assets, fname), "wb") as fh:
            fh.write(fetch(url))
        out.append(block.replace(url, fname))
        n += 1
    with open(os.path.join(assets, "fonts.css"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--bpm", type=float, default=120)
    ap.add_argument("--beats", type=float, default=32)
    ap.add_argument("--name", default="video")
    ap.add_argument("--fonts")
    args = ap.parse_args()
    os.makedirs(os.path.join(args.folder, "assets"), exist_ok=True)
    for f in os.listdir(ENGINE):
        target = os.path.join(args.folder, f)
        if not os.path.exists(target):
            shutil.copy(os.path.join(ENGINE, f), target)
    tl_path = os.path.join(args.folder, "timeline.json")
    with open(tl_path, encoding="utf-8") as fh:
        tl = json.load(fh)
    w, h = (int(x) for x in args.size.lower().split("x"))
    tl.update(name=args.name, width=w, height=h, fps=args.fps, bpm=args.bpm, beats=args.beats)
    tl["tools"] = os.path.dirname(os.path.abspath(__file__))
    fonts = ""
    css = os.path.join(args.folder, "assets", "fonts.css")
    if not os.path.exists(css):
        open(css, "w").close()
    if args.fonts:
        try:
            fonts = f", {google_fonts(args.fonts, os.path.join(args.folder, 'assets'))} font files in assets/fonts.css"
        except Exception as exc:
            fonts = f", fonts failed ({exc}); put woff2 files in assets/ and @font-face rules in assets/fonts.css"
    with open(tl_path, "w", encoding="utf-8") as fh:
        json.dump(tl, fh, indent=2)
    print(f"{args.folder}: index.html, timeline.json, render.py, synth.py, assets/  ({w}x{h}, {args.fps} fps, {args.bpm} bpm, {args.beats} beats = {args.beats * 60 / args.bpm:.2f} s){fonts}")


if __name__ == "__main__":
    main()
