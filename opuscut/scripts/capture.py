"""Capture a real page (the product's own app, 3D scene or animation) frame by frame under a virtual clock.

  python capture.py <url-or-path> --out plates/house --seconds 6 [--fps 30] [--size 1920x1080]
                    [--serve DIR] [--mount assets=DIR ...] [--wait "window.ready === true"]
                    [--actions actions.json] [--selector canvas] [--transparent] [--mp4]

The page's requestAnimationFrame, performance.now, Date and timers run on a clock that advances exactly
1/fps per frame, so the product's own animation code renders frame-exact. actions.json is a list of
{"at": seconds, "js": "code"} evaluated before the frame at that time.
Needs Python with playwright (chromium) and, for --mp4, ffmpeg.
"""
import argparse
import asyncio
import functools
import http.server
import json
import os
import shutil
import subprocess
import threading
import time

from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))


def serve(root, mounts):
    table = sorted((("/" + p.replace("\\", "/").rsplit(":", 1)[-1].split("/Git/")[-1].strip("/")).rstrip("/") or "/", os.path.abspath(d)) for p, d in mounts)
    table.sort(key=lambda m: -len(m[0]))

    class Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript", ".mjs": "text/javascript", ".glb": "model/gltf-binary", ".wasm": "application/wasm"}

        def log_message(self, *a, **k):
            pass

        def translate_path(self, path):
            clean = path.split("?", 1)[0].split("#", 1)[0]
            for prefix, directory in table:
                if prefix == "/" or clean == prefix or clean.startswith(prefix + "/"):
                    rest = clean[len(prefix):] if prefix != "/" else clean
                    return os.path.join(directory, *[p for p in rest.split("/") if p and p != ".."])
            return os.path.join(root, *[p for p in clean.split("/") if p and p != ".."])

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=root))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--serve")
    ap.add_argument("--mount", action="append", default=[])
    ap.add_argument("--wait", default="document.readyState === 'complete'")
    ap.add_argument("--settle", type=float, default=0.5)
    ap.add_argument("--actions")
    ap.add_argument("--selector")
    ap.add_argument("--transparent", action="store_true")
    ap.add_argument("--mp4", action="store_true")
    args = ap.parse_args()

    w, h = (int(x) for x in args.size.lower().split("x"))
    os.makedirs(args.out, exist_ok=True)
    actions = json.load(open(args.actions, encoding="utf-8")) if args.actions else []
    actions.sort(key=lambda a: a["at"])

    srv = None
    url = args.target
    if not url.startswith(("http://", "https://")):
        root = os.path.abspath(args.serve or os.path.dirname(os.path.abspath(url)))
        mounts = [m.split("=", 1) for m in args.mount]
        if os.path.exists(url):
            page_file = os.path.abspath(url)
            if os.path.commonpath([root, page_file]) == root:
                rel = os.path.relpath(page_file, root).replace(os.sep, "/")
            else:
                mounts.append(("/__page", os.path.dirname(page_file)))
                rel = "__page/" + os.path.basename(page_file)
        else:
            rel = url.lstrip("/")
        srv, base = serve(root, mounts)
        url = f"{base}/{rel}"

    ext, fmt = (".png", "png") if args.transparent else (".jpg", "jpeg")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(channel="chromium", headless=True, args=["--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=default"])
        except Exception:
            browser = await p.chromium.launch(headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = await browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        page.on("pageerror", lambda e: print("[page error]", e))
        page.on("response", lambda r: print("[404]", r.url) if r.status == 404 else None)
        page.on("console", lambda m: print("[page]", m.text) if m.type in ("error", "warning") else None)
        await page.add_init_script(path=os.path.join(HERE, "virtual_clock.js"))
        await page.goto(url)
        deadline = time.time() + 180
        while not await page.evaluate(f"() => !!({args.wait})"):
            if time.time() > deadline:
                raise SystemExit(f"timed out waiting for: {args.wait}")
            await asyncio.sleep(0.25)
        await page.wait_for_timeout(int(args.settle * 1000))
        await page.evaluate("window.__clock.start()")
        target = page.locator(args.selector).first if args.selector else page
        total = round(args.seconds * args.fps)
        step = 1000 / args.fps
        k = 0
        t0 = time.time()
        for n in range(total):
            t = n / args.fps
            while k < len(actions) and actions[k]["at"] <= t + 1e-9:
                await page.evaluate(actions[k]["js"])
                k += 1
            await page.evaluate(f"window.__clock.advance({step})")
            await target.screenshot(path=os.path.join(args.out, f"{n:05d}{ext}"), type=fmt, omit_background=args.transparent, **({} if args.transparent else {"quality": 92}))
            if (n + 1) % args.fps == 0:
                print(f"  {n + 1}/{total} frames  {time.time() - t0:5.1f}s", flush=True)
        await browser.close()
    if srv:
        srv.shutdown()
    with open(os.path.join(args.out, "plate.json"), "w", encoding="utf-8") as fh:
        json.dump({"frames": total, "fps": args.fps, "ext": ext[1:], "width": w, "height": h}, fh)
    print(f"{total} frames in {args.out} ({ext[1:]}, {args.fps} fps)")
    if args.mp4 and shutil.which("ffmpeg"):
        mp4 = args.out.rstrip("/\\") + ".mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(args.fps), "-i", os.path.join(args.out, f"%05d{ext}"),
                        "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", mp4], check=True)
        print("preview:", mp4)


if __name__ == "__main__":
    asyncio.run(main())
