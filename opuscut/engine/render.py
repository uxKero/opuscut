"""Render index.html frame by frame with headless Chromium and encode it with ffmpeg.

  python render.py                     full render to out/<name>.mp4 with out/sound.wav at -14 LUFS, then QA and a self-measure
  python render.py --frames 60 400     save single frames to out/frames/
  python render.py --beats             one frame per beat plus a contact sheet at out/beats.png
  python render.py --from 8 --to 16    render a range of beats (silent)
  python render.py --workers 4         parallel pages (default 6)

Needs Python with playwright (chromium installed), Pillow, and ffmpeg on PATH.
"""
import argparse
import asyncio
import base64
import functools
import http.server
import io
import json
import math
import os
import shutil
import subprocess
import threading
import time

from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        raise SystemExit("ffmpeg not found on PATH")
    return exe


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/index.html"


async def open_page(browser, url, w, h):
    page = await browser.new_page(viewport={"width": w, "height": h})
    page.on("console", lambda m: print("[page]", m.text) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: print("[page error]", e))
    await page.goto(url)
    await page.wait_for_function("window.__ready === true", timeout=120000)
    return page


async def grab(page, n, fmt):
    data = await page.evaluate("([n, f]) => window.renderFrame(n, f)", [n, fmt])
    return base64.b64decode(data.split(",", 1)[1])


def contact_sheet(images, labels, path, cols=6, width=480):
    from PIL import Image, ImageDraw
    tiles = [Image.open(io.BytesIO(b)).convert("RGB") for b in images]
    h = int(width * tiles[0].height / tiles[0].width)
    rows = math.ceil(len(tiles) / cols)
    pad, lh = 6, 24
    sheet = Image.new("RGB", (cols * (width + pad) + pad, rows * (h + lh + pad) + pad), (18, 18, 18))
    d = ImageDraw.Draw(sheet)
    for i, (t, label) in enumerate(zip(tiles, labels)):
        x, y = pad + (i % cols) * (width + pad), pad + (i // cols) * (h + lh + pad)
        sheet.paste(t.resize((width, h), Image.LANCZOS), (x, y))
        d.text((x + 3, y + h + 4), label, fill=(230, 230, 230))
    sheet.save(path)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", nargs="*", type=int)
    ap.add_argument("--beats", action="store_true")
    ap.add_argument("--from", dest="start", type=float)
    ap.add_argument("--to", dest="end", type=float)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    with open(os.path.join(ROOT, "timeline.json"), encoding="utf-8") as fh:
        tl = json.load(fh)
    fps, w, h, name = tl["fps"], tl["width"], tl["height"], tl.get("name", "video")
    spb = 60 / tl["bpm"]
    total = round(tl["beats"] * spb * fps)
    os.makedirs(OUT, exist_ok=True)
    srv, url = serve()

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(channel="chromium", headless=True, args=["--enable-gpu", "--ignore-gpu-blocklist"])
        except Exception:
            browser = await p.chromium.launch(headless=True)
        if args.frames or args.beats:
            page = await open_page(browser, url, w, h)
            if args.beats:
                picks = [min(total - 1, round((b + 0.5) * spb * fps)) for b in range(int(tl["beats"]))]
                shots = [await grab(page, n, "jpeg") for n in picks]
                contact_sheet(shots, [f"beat {b}  {n / fps:.2f}s" for b, n in enumerate(picks)], os.path.join(OUT, "beats.png"))
                print(os.path.join(OUT, "beats.png"))
            if args.frames:
                fdir = os.path.join(OUT, "frames")
                os.makedirs(fdir, exist_ok=True)
                for n in args.frames:
                    path = os.path.join(fdir, f"f{n:05d}.png")
                    with open(path, "wb") as fh:
                        fh.write(await grab(page, n, "png"))
                    print(path)
            await browser.close()
            srv.shutdown()
            return

        first = round(args.start * spb * fps) if args.start is not None else 0
        last = round(args.end * spb * fps) if args.end is not None else total
        ranged = args.start is not None or args.end is not None
        video = os.path.join(OUT, f"{name}-range.mp4" if ranged else f"{name}-silent.mp4")
        ff = subprocess.Popen(
            [ffmpeg(), "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
             "-vf", "scale=in_range=full:out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-color_range", "tv", "-r", str(fps), "-movflags", "+faststart", video],
            stdin=subprocess.PIPE,
        )
        pages = await asyncio.gather(*[open_page(browser, url, w, h) for _ in range(args.workers)])
        results, nxt, t0 = {}, first, time.time()
        lock = asyncio.Lock()

        async def worker(page):
            nonlocal nxt
            while True:
                async with lock:
                    n = nxt
                    nxt += 1
                if n >= last:
                    return
                while len(results) > 60:
                    await asyncio.sleep(0.01)
                results[n] = await grab(page, n, "jpeg")

        async def writer():
            n = first
            while n < last:
                if n in results:
                    ff.stdin.write(results.pop(n))
                    n += 1
                    if (n - first) % fps == 0:
                        el = time.time() - t0
                        print(f"  {n - first}/{last - first} frames  {el:5.1f}s", flush=True)
                else:
                    await asyncio.sleep(0.005)

        await asyncio.gather(writer(), *[worker(pg) for pg in pages])
        ff.stdin.close()
        ff.wait()
        await browser.close()
    srv.shutdown()
    print(f"picture: {last - first} frames in {time.time() - t0:.1f}s -> {video}")

    wav = os.path.join(OUT, "sound.wav")
    if ranged:
        return
    final = os.path.join(OUT, f"{name}.mp4")
    if os.path.exists(wav):
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a",
                        "-af", f"loudnorm=I=-14:TP=-2.5:LRA=11,aresample=48000,afade=t=out:st={max(0, tl['beats'] * spb - 0.5):.3f}:d=0.5", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                        "-shortest", "-movflags", "+faststart", final], check=True)
    else:
        shutil.copy(video, final)
        print("no out/sound.wav: the video is silent")
    print("final:", final)
    tools = tl.get("tools")
    if tools and os.path.isdir(tools):
        import sys
        qa = subprocess.run([sys.executable, os.path.join(tools, "qa.py"), final, "--expect-seconds", f"{tl['beats'] * spb:.3f}"], capture_output=True, text=True)
        print("qa:", (qa.stdout + qa.stderr).strip())
        subprocess.run([sys.executable, os.path.join(tools, "analyze_reference.py"), final, "--out", os.path.join(OUT, "self")], capture_output=True)
        md = os.path.join(OUT, "self", "analysis.md")
        if os.path.exists(md):
            keep = [l for l in open(md, encoding="utf-8").read().splitlines() if l.startswith("- ") and any(k in l for k in ("shots:", "spread", "tempo", "first half"))]
            print("self-measure:\n" + "\n".join(keep))
            data = json.load(open(os.path.join(OUT, "self", "analysis.json"), encoding="utf-8"))
            p = data.get("pace") or {}
            if p.get("churn") and str(tl.get("pace", "")).lower() not in ("frantic", "lively"):
                print(f"pace warning: the image rarely settles ({int(p['change_share'] * 100)}% of the time with large motion, cuts or transitions, "
                      f"longest settled stretch {p['longest_settle_s']} s, holds cover {int(p['hold_share'] * 100)}%). "
                      "Constant scene changes are the stock pace; give the key moments a hold unless a lively or frantic pace was chosen.")


if __name__ == "__main__":
    asyncio.run(main())
