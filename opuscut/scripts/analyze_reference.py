"""Measure a reference video or a set of images and write analysis.json, analysis.md and contact sheets.

Usage:
  python analyze_reference.py <video | image | folder | url> [--out DIR] [--sheet-every SECONDS]

Needs numpy, Pillow and ffmpeg/ffprobe on PATH. yt-dlp only for URLs.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
AUDIO_EXT = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}
MOTION_W = 160
STYLE_W = 384
MAX_MOTION_FRAMES = 5400


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, check=True, **kw)


def need(tool):
    if not shutil.which(tool):
        sys.exit(f"{tool} not found on PATH")


def fetch_url(url, out):
    need("yt-dlp")
    target = os.path.join(out, "reference.%(ext)s")
    run(["yt-dlp", "-f", "b[height<=720]/bv*[height<=720]+ba/b", "--merge-output-format", "mp4", "-o", target, url])
    for f in os.listdir(out):
        if f.startswith("reference."):
            return os.path.join(out, f)
    sys.exit("download failed")


def probe(path):
    data = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path]).stdout)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    num, den = video.get("avg_frame_rate", "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "fps": round(fps, 3),
        "duration": float(data["format"].get("duration", video.get("duration", 0))),
        "has_audio": any(s["codec_type"] == "audio" for s in data["streams"]),
    }


def decode(path, width, height, fps=None, gray=False):
    vf = f"scale={width}:{height}:flags=area"
    if fps:
        vf = f"fps={fps}," + vf
    fmt, ch = ("gray", 1) if gray else ("rgb24", 3)
    raw = run(["ffmpeg", "-v", "error", "-i", path, "-vf", vf, "-f", "rawvideo", "-pix_fmt", fmt, "-"]).stdout
    frames = np.frombuffer(raw, np.uint8)
    n = frames.size // (width * height * ch)
    return frames[: n * width * height * ch].reshape(n, height, width, ch) if ch == 3 else frames[: n * width * height].reshape(n, height, width)


def even(x):
    return max(2, int(round(x / 2)) * 2)


def detect_cuts(rgb, fps):
    q = (rgb >> 5).astype(np.int32)
    codes = (q[..., 0] << 6) | (q[..., 1] << 3) | q[..., 2]
    n = len(rgb)
    hists = np.zeros((n, 512), np.float32)
    for i in range(n):
        hists[i] = np.bincount(codes[i].ravel(), minlength=512)
    hists /= hists.sum(1, keepdims=True)
    hist_d = np.abs(np.diff(hists, axis=0)).sum(1) / 2
    gray = rgb.mean(-1)
    pix_d = np.abs(np.diff(gray, axis=0)).mean((1, 2)) / 255
    score = hist_d * 0.6 + np.minimum(pix_d * 4, 1) * 0.4
    k = max(3, int(fps * 0.5))
    candidates = []
    for i in range(len(score)):
        lo, hi = max(0, i - k), min(len(score), i + k + 1)
        local = np.delete(score[lo:hi], i - lo)
        base = np.median(local) if local.size else 0
        if score[i] > 0.28 and score[i] > base * 3 + 0.08 and score[i] == score[lo:hi].max():
            candidates.append(i + 1)
    cuts, flashes = [], []
    for c in candidates:
        if c + 1 < n and 0 < c and np.abs(gray[c - 1] - gray[c + 1]).mean() / 255 < 0.04:
            flashes.append(c)
        else:
            cuts.append(c)
    return cuts, flashes, pix_d


def detect_soft_transitions(rgb, fps, cuts):
    q = (rgb >> 5).astype(np.int32)
    codes = (q[..., 0] << 6) | (q[..., 1] << 3) | q[..., 2]
    hists = np.stack([np.bincount(c.ravel(), minlength=512) for c in codes]).astype(np.float32)
    hists /= hists.sum(1, keepdims=True)
    k = max(2, int(round(fps * 0.3)))
    far = np.zeros(len(rgb))
    for i in range(k, len(rgb) - k):
        far[i] = np.abs(hists[i + k] - hists[i - k]).sum() / 2
    found = []
    guard = int(fps * 0.6)
    for i in range(k, len(rgb) - k):
        if far[i] < 0.3 or far[i] < far[max(0, i - guard): i + guard + 1].max():
            continue
        if any(abs(i - c) <= guard for c in cuts) or any(abs(i - f) <= guard for f in found):
            continue
        found.append(i)
    return found, far


def pace_profile(rgb, far, cuts, fps, duration):
    n = len(far)
    g = rgb.mean(-1)
    h, w = g.shape[1] // 2 * 2, g.shape[2] // 2 * 2
    small = g[:, :h, :w].reshape(n, h // 2, 2, w // 2, 2).mean((2, 4))
    moving_area = np.concatenate([[0.0], (np.abs(np.diff(small, axis=0)) > 10).mean((1, 2))])
    changing = (far > 0.2) | (moving_area >= 0.05)
    for c in cuts:
        changing[max(0, c - 1):min(n, c + 1)] = True
    runs, start = [], None
    for i in range(n + 1):
        calm = i < n and not changing[i]
        if calm and start is None:
            start = i
        elif not calm and start is not None:
            runs.append((i - start) / fps)
            start = None
    hold_min = min(3.0, max(1.2, 0.12 * duration))
    holds = [r for r in runs if r >= hold_min]
    longest = max(runs) if runs else 0.0
    hold_share = sum(holds) / duration if duration else 0.0
    return {
        "change_share": round(float(changing.mean()), 2),
        "longest_settle_s": round(longest, 2),
        "hold_min_s": round(hold_min, 2),
        "holds": len(holds),
        "hold_share": round(hold_share, 2),
        "churn": bool(longest < hold_min or hold_share < 0.25 or changing.mean() > 0.45),
    }


def shot_stats(cuts, n_frames, fps):
    bounds = [0] + cuts + [n_frames]
    lengths = [(b - a) / fps for a, b in zip(bounds, bounds[1:]) if b > a]
    if not lengths:
        return {}, []
    arr = np.array(lengths)
    duration = n_frames / fps
    window = 5.0
    per_window = []
    t = 0.0
    while t < duration - 1e-6:
        per_window.append(sum(1 for c in cuts if t <= c / fps < t + window))
        t += window
    half = duration / 2
    first = [l for a, l in zip(bounds, lengths) if a / fps < half]
    second = [l for a, l in zip(bounds, lengths) if a / fps >= half]
    stats = {
        "shots": len(lengths),
        "cuts": len(cuts),
        "cuts_per_minute": round(len(cuts) / duration * 60, 1) if duration else 0,
        "average_shot_s": round(float(arr.mean()), 2),
        "median_shot_s": round(float(np.median(arr)), 2),
        "shortest_s": round(float(arr.min()), 2),
        "longest_s": round(float(arr.max()), 2),
        "spread": round(float(arr.max() / max(arr.min(), 1 / fps)), 1),
        "cuts_per_5s": per_window,
        "average_shot_first_half_s": round(float(np.mean(first)), 2) if first else None,
        "average_shot_second_half_s": round(float(np.mean(second)), 2) if second else None,
    }
    return stats, [round(x, 3) for x in lengths]


def global_shift(a, b):
    fa, fb = np.fft.fft2(a), np.fft.fft2(b)
    r = fa * np.conj(fb)
    r /= np.abs(r) + 1e-9
    corr = np.fft.ifft2(r).real
    peak = np.unravel_index(np.argmax(corr), corr.shape)
    dy, dx = [p - s if p > s // 2 else p for p, s in zip(peak, corr.shape)]
    return dx, dy, float(corr.max())


def motion_profile(gray_small, fps, cuts, flashes, duration):
    skip = set(cuts) | set(flashes) | {c + 1 for c in flashes}
    diffs = np.abs(np.diff(gray_small.astype(np.float32), axis=0)).mean((1, 2)) / 255
    valid = np.array([i + 1 not in skip for i in range(len(diffs))])
    energy_per_s = []
    for s in range(int(math.ceil(duration))):
        lo, hi = int(s * fps), int((s + 1) * fps)
        sel = diffs[lo:hi][valid[lo:hi]]
        energy_per_s.append(round(float(sel.mean() * 100), 2) if sel.size else 0.0)
    moving = valid & (diffs > 0.004)
    held = valid & (diffs < 0.0015)
    runs, run = [], 0
    for i in range(len(diffs)):
        if held[i]:
            run += 1
        elif run:
            runs.append(run + 1)
            run = 0
    neighbours_move = [i for i in range(1, len(diffs) - 1) if held[i] and (diffs[i - 1] > 0.004 or diffs[i + 1] > 0.004)]
    step = max(1, int(round(fps / 6)))
    pans, samples = 0, 0
    for i in range(0, len(gray_small) - step, step):
        if any(c in range(i + 1, i + step + 1) for c in cuts):
            continue
        dx, dy, conf = global_shift(gray_small[i].astype(np.float32), gray_small[i + step].astype(np.float32))
        samples += 1
        if conf > 0.12 and (abs(dx) + abs(dy)) >= 1:
            pans += 1
    stepped = [r for r in runs if 2 <= r <= 4]
    cadence = None
    if len(neighbours_move) > 0.15 * max(1, moving.sum()) and stepped:
        cadence = f"on {int(np.bincount(stepped).argmax())}s"
    return {
        "energy_per_second": energy_per_s,
        "energy_mean": round(float(diffs[valid].mean() * 100), 2) if valid.any() else 0,
        "moving_fraction": round(float(moving.sum() / max(1, valid.sum())), 2),
        "held_fraction": round(float(held.sum() / max(1, valid.sum())), 2),
        "stepped_cadence": cadence,
        "camera_translation_fraction": round(pans / samples, 2) if samples else 0,
        "flashes": len(flashes),
    }


def kmeans(pixels, k=6, iters=12, seed=7):
    rng = np.random.default_rng(seed)
    centers = pixels[rng.choice(len(pixels), k, replace=False)].astype(np.float32)
    for _ in range(iters):
        d = ((pixels[:, None, :] - centers[None]) ** 2).sum(-1)
        label = d.argmin(1)
        for j in range(k):
            sel = pixels[label == j]
            if len(sel):
                centers[j] = sel.mean(0)
    counts = np.bincount(label, minlength=k)
    order = np.argsort(-counts)
    return centers[order], counts[order] / counts.sum()


def hexcolor(c):
    return "#%02x%02x%02x" % tuple(int(round(v)) for v in c)


def palette(frames, k=6):
    px = np.concatenate([f.reshape(-1, 3)[:: max(1, f.shape[0] * f.shape[1] // 4000)] for f in frames]).astype(np.float32)
    centers, share = kmeans(px, k)
    return [{"hex": hexcolor(c), "share": round(float(s), 3)} for c, s in zip(centers, share) if s > 0.01]


def style_signals(frame):
    f = frame.astype(np.float32)
    lum = f @ np.array([0.299, 0.587, 0.114], np.float32)
    q = (frame >> 4).astype(np.int32)
    codes = (q[..., 0] << 8) | (q[..., 1] << 4) | q[..., 2]
    counts = np.sort(np.bincount(codes.ravel(), minlength=4096))[::-1]
    colors95 = int(np.searchsorted(np.cumsum(counts), 0.95 * counts.sum()) + 1)
    gy, gx = np.gradient(lum)
    mag = np.hypot(gx, gy)
    flat = float((mag < 1.0).mean())
    ramp = float(((mag >= 1.0) & (mag < 6)).mean())
    strong = mag > 40
    edge_density = float(strong.mean())
    dark_outline = float((lum[strong] < 70).mean()) if strong.any() else 0.0
    lap = np.abs(4 * lum[1:-1, 1:-1] - lum[:-2, 1:-1] - lum[2:, 1:-1] - lum[1:-1, :-2] - lum[1:-1, 2:])
    calm = mag[1:-1, 1:-1] < 6
    grain = float(lap[calm].mean()) if calm.any() else 0.0
    ang = (np.degrees(np.arctan2(gy, gx))[strong] + 90) % 180
    w = mag[strong]
    hist = np.bincount((ang // 5).astype(int) % 36, weights=w, minlength=36)
    hist = hist / hist.sum() if hist.sum() else hist

    def mass(center, width=7.5):
        return float(sum(hist[b] for b in range(36) if min(abs(b * 5 + 2.5 - center), 180 - abs(b * 5 + 2.5 - center)) <= width))

    hsv_max = f.max(-1)
    sat = np.where(hsv_max > 0, (hsv_max - f.min(-1)) / np.maximum(hsv_max, 1), 0)
    return {
        "colors_95": colors95,
        "flat_fraction": round(flat, 3),
        "ramp_fraction": round(ramp, 3),
        "edge_density": round(edge_density, 4),
        "dark_outline_share": round(dark_outline, 3),
        "grain": round(grain, 2),
        "lines_axis": round(mass(0) + mass(90), 3),
        "lines_iso": round(mass(30) + mass(150), 3),
        "lines_other": round(max(0.0, 1 - mass(0) - mass(90) - mass(30) - mass(150)), 3),
        "luminance": round(float(lum.mean() / 255), 3),
        "saturation": round(float(sat.mean()), 3),
        "contrast": round(float(lum.std() / 255), 3),
    }


def summarize_style(signals):
    keys = signals[0].keys()
    return {k: round(float(np.median([s[k] for s in signals])), 4) for k in keys}


def read_style(s):
    notes = []
    if s["colors_95"] < 90 and s["flat_fraction"] > 0.55:
        notes.append("flat fills with few colors: vector, flat illustration or UI")
    elif s["colors_95"] > 700 and s["flat_fraction"] < 0.2:
        notes.append("continuous tone: live action, photoreal 3D or painted")
    elif s["ramp_fraction"] > 0.35:
        notes.append("smooth ramps dominate: soft shading, gradients or rendered 3D")
    else:
        notes.append("mixed: stylized 3D, textured illustration or composited")
    if s["dark_outline_share"] > 0.45 and s["edge_density"] > 0.01:
        notes.append("dark outlines on shapes: cartoon or inked line work")
    if s["lines_iso"] > 0.2 and s["lines_iso"] > s["lines_other"] * 0.5:
        notes.append("strong 30/150 degree lines: likely isometric or axonometric")
    elif s["lines_axis"] > 0.6:
        notes.append("mostly horizontal and vertical lines: frontal, grid, editorial or UI")
    if s["grain"] > 3.0:
        notes.append("visible grain or paper texture in flat areas")
    notes.append("light key" if s["luminance"] > 0.6 else "dark key" if s["luminance"] < 0.3 else "mid key")
    notes.append("saturated" if s["saturation"] > 0.45 else "muted" if s["saturation"] < 0.2 else "moderate saturation")
    return notes


def read_rhythm(stats, motion, duration):
    notes = []
    if not stats or stats["cuts"] == 0:
        notes.append("no shot changes: one continuous take")
    else:
        if stats["soft_transitions"] > stats["hard_cuts"]:
            notes.append("scenes change mostly through transitions, not hard cuts")
        if stats["cuts"] <= max(2, duration / 8):
            notes.append("few cuts for the length: camera moves and in-frame changes carry it")
        if stats["spread"] >= 20:
            notes.append(f"wide shot-length spread ({stats['spread']}x): holds and bursts")
        elif stats["spread"] < 4:
            notes.append(f"narrow spread ({stats['spread']}x): even, list-like cutting")
        a, b = stats["average_shot_first_half_s"], stats["average_shot_second_half_s"]
        if a and b:
            if b < a * 0.7:
                notes.append("cutting accelerates toward the end")
            elif b > a * 1.4:
                notes.append("cutting slows toward the end: decelerates into a hold")
    if motion["stepped_cadence"]:
        notes.append(f"held drawings between moves: animated {motion['stepped_cadence']}")
    if motion["camera_translation_fraction"] > 0.35:
        notes.append("the camera travels often: pans, tracks or scrolling layers")
    if motion["flashes"]:
        notes.append(f"{motion['flashes']} single-frame flashes: impact frames")
    e = motion["energy_per_second"]
    if len(e) >= 4:
        peak = int(np.argmax(e))
        notes.append(f"motion peaks at {peak}s of {len(e)}s")
    return notes


def audio_profile(path, duration, cut_times):
    sr = 22050
    raw = run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]).stdout
    y = np.frombuffer(raw, np.float32)
    if y.size < sr:
        return None
    hop, win = 512, 2048
    n = 1 + (len(y) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    spec = np.abs(np.fft.rfft(y[idx] * np.hanning(win), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(spec), axis=0)).sum(1)
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    env_fps = sr / hop
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lags = np.arange(len(ac))
    bpm_axis = 60 * env_fps / np.maximum(lags, 1)
    band = (bpm_axis >= 70) & (bpm_axis <= 180)
    if not band.any():
        return None
    lag = int(lags[band][np.argmax(ac[band])])
    coarse = 60 * env_fps / lag
    best = (-1e9, coarse, 0.0)
    for bpm in np.arange(coarse - 3, coarse + 3, 0.05):
        period = 60 / bpm
        beats = np.arange(0, len(y) / sr - period, period)
        for phase in np.arange(0, period, 1 / env_fps):
            idx = np.round((beats + phase) * env_fps).astype(int)
            idx = idx[idx < len(flux)]
            score = flux[idx].mean()
            if score > best[0]:
                best = (score, bpm, phase)
    _, bpm, beat0 = best
    period = 60 / bpm
    beat0 = (beat0 + (hop + win / 2) / sr) % period
    on_beat = None
    if cut_times:
        tol = 0.06
        hits = sum(1 for t in cut_times if min((t - beat0) % period, period - (t - beat0) % period) <= tol)
        on_beat = {"share": round(hits / len(cut_times), 2), "by_chance": round(float(min(1.0, 2 * tol / period)), 2)}
    rms = []
    for sec in range(int(math.ceil(duration))):
        seg = y[sec * sr:(sec + 1) * sr]
        rms.append(round(float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-6)), 1) if seg.size else -120.0)
    frame = int(sr * 0.01)
    blocks = len(y) // frame
    level = 20 * np.log10(np.sqrt((y[: blocks * frame].reshape(blocks, frame) ** 2).mean(1)) + 1e-9)
    floor = min(-50.0, float(np.median(level)) - 35)
    gaps, start = [], None
    for i, db in enumerate(level):
        if db < floor and start is None:
            start = i
        elif db >= floor and start is not None:
            if (i - start) * 0.01 >= 0.04 and start * 0.01 > 0.3:
                gaps.append({"at_s": round(start * 0.01, 2), "length_s": round((i - start) * 0.01, 2)})
            start = None
    return {
        "bpm": round(float(bpm), 1),
        "first_beat_s": round(float(beat0), 3),
        "changes_on_beat": on_beat,
        "loudness_db_per_second": rms,
        "silences_at_s": gaps[:12],
    }


def load_font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def sheet(images, labels, path, cols=5, width=360):
    if not images:
        return
    h = int(width * images[0].shape[0] / images[0].shape[1])
    rows = math.ceil(len(images) / cols)
    pad, label_h = 6, 22
    canvas = Image.new("RGB", (cols * (width + pad) + pad, rows * (h + label_h + pad) + pad), (18, 18, 18))
    draw = ImageDraw.Draw(canvas)
    font = load_font(14)
    for i, (img, label) in enumerate(zip(images, labels)):
        x = pad + (i % cols) * (width + pad)
        y = pad + (i // cols) * (h + label_h + pad)
        canvas.paste(Image.fromarray(img).resize((width, h), Image.LANCZOS), (x, y))
        draw.text((x + 2, y + h + 3), label, fill=(230, 230, 230), font=font)
    canvas.save(path)


def fmt_t(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def analyze_video(path, out, sheet_every):
    meta = probe(path)
    fps = meta["fps"] or 30
    duration = meta["duration"]
    aspect = meta["height"] / meta["width"]
    motion_fps = fps if duration * fps <= MAX_MOTION_FRAMES else MAX_MOTION_FRAMES / duration
    mh = even(MOTION_W * aspect)
    rgb_small = decode(path, MOTION_W, mh, None if motion_fps == fps else motion_fps)
    cuts, flashes, _ = detect_cuts(rgb_small, motion_fps)
    soft, far = detect_soft_transitions(rgb_small, motion_fps, cuts)
    pace = pace_profile(rgb_small, far, cuts, motion_fps, duration)
    stats, lengths = shot_stats(sorted(cuts + soft), len(rgb_small), motion_fps)
    stats["hard_cuts"] = len(cuts)
    stats["soft_transitions"] = len(soft)
    gray_small = rgb_small.mean(-1).astype(np.uint8)
    motion = motion_profile(gray_small, motion_fps, cuts, flashes, duration)
    cut_times = [round(c / motion_fps, 3) for c in cuts]
    soft_times = [round(c / motion_fps, 3) for c in soft]

    sh = even(STYLE_W * aspect)
    bounds = [0] + sorted(cuts + soft) + [len(rgb_small)]
    mids = [((a + b) / 2) / motion_fps for a, b in zip(bounds, bounds[1:]) if b > a]
    style_frames, shot_palettes = [], []
    for t in mids[:60]:
        raw = run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", f"scale={STYLE_W}:{sh}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]).stdout
        if len(raw) >= STYLE_W * sh * 3:
            f = np.frombuffer(raw[: STYLE_W * sh * 3], np.uint8).reshape(sh, STYLE_W, 3)
            style_frames.append((t, f))
    for t, f in style_frames:
        shot_palettes.append({"at_s": round(t, 2), "colors": palette([f], 4)})
    signals = [style_signals(f) for _, f in style_frames]
    style = summarize_style(signals) if signals else {}
    global_palette = palette([f for _, f in style_frames]) if style_frames else []

    audio = audio_profile(path, duration, cut_times) if meta["has_audio"] else None

    sheet([f for _, f in style_frames], [f"shot {i + 1}  {fmt_t(t)}" for i, (t, _) in enumerate(style_frames)], os.path.join(out, "shots.png"))
    every = sheet_every or max(0.5, duration / 30)
    uniform = decode(path, STYLE_W, sh, 1 / every)
    sheet(list(uniform), [fmt_t(i * every) for i in range(len(uniform))], os.path.join(out, "timeline.png"), cols=6)

    return {
        "source": path,
        "kind": "video",
        "meta": meta,
        "shots": stats,
        "shot_lengths_s": lengths,
        "cut_times_s": cut_times,
        "soft_transition_times_s": soft_times,
        "motion": motion,
        "audio": audio,
        "style": style,
        "style_reading": read_style(style) if style else [],
        "pace": pace,
        "rhythm_reading": read_rhythm(stats, motion, duration) + ([f"the image rarely settles: {int(pace['change_share'] * 100)}% of the time something large is moving, cutting or transitioning, and the longest settled stretch is {pace['longest_settle_s']} s"] if pace["churn"] else [f"it settles: {pace['holds']} holds of {pace['hold_min_s']} s or more, {int(pace['hold_share'] * 100)}% of the time"]),
        "palette": global_palette,
        "shot_palettes": shot_palettes,
        "sheets": ["shots.png", "timeline.png"],
    }


def analyze_images(paths, out):
    frames = []
    for p in paths:
        img = Image.open(p).convert("RGB")
        img.thumbnail((STYLE_W * 2, STYLE_W * 2))
        w = STYLE_W
        h = even(w * img.height / img.width)
        frames.append(np.asarray(img.resize((w, h), Image.LANCZOS)))
    signals = [style_signals(f) for f in frames]
    style = summarize_style(signals)
    same = [f for f in frames if f.shape == frames[0].shape]
    sheet(same, [os.path.basename(p) for p, f in zip(paths, frames) if f.shape == frames[0].shape], os.path.join(out, "images.png"), cols=4)
    return {
        "source": paths,
        "kind": "images",
        "style": style,
        "style_per_image": signals,
        "style_reading": read_style(style),
        "palette": palette(frames),
        "sheets": ["images.png"],
    }


def analyze_audio(path):
    data = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-of", "json", path]).stdout)
    duration = float(data["format"]["duration"])
    return {"source": path, "kind": "audio", "duration": round(duration, 3), "audio": audio_profile(path, duration, [])}


def write_md(result, out):
    if result["kind"] == "audio":
        a = result["audio"] or {}
        lines = ["# Audio analysis", "", f"Source: `{result['source']}`, {result['duration']} s", "",
                 f"- tempo about {a.get('bpm')} BPM, first beat {a.get('first_beat_s')} s",
                 f"- silences at: {a.get('silences_at_s')}",
                 f"- loudness dB per second: {a.get('loudness_db_per_second')}"]
        with open(os.path.join(out, "analysis.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        return

    lines = ["# Reference analysis", "", f"Source: `{result['source']}`", ""]
    if result["kind"] == "video":
        m = result["meta"]
        lines += [f"{m['width']}x{m['height']}, {m['fps']} fps, {m['duration']:.2f} s, audio: {'yes' if m['has_audio'] else 'no'}", ""]
        s = result["shots"]
        if s:
            lines += ["## Cutting", "",
                      f"- {s['shots']} shots: {s['hard_cuts']} hard cuts and {s['soft_transitions']} soft transitions (wipes, dissolves, masks), {s['cuts_per_minute']} changes per minute",
                      f"- hard cuts at {result['cut_times_s']} s, soft transitions at {result['soft_transition_times_s']} s",
                      f"- average {s['average_shot_s']} s, median {s['median_shot_s']} s, shortest {s['shortest_s']} s, longest {s['longest_s']} s, spread {s['spread']}x",
                      f"- first half average {s['average_shot_first_half_s']} s, second half {s['average_shot_second_half_s']} s",
                      f"- cuts per 5 s: {s['cuts_per_5s']}",
                      f"- shot lengths: {result['shot_lengths_s']}", ""]
        mo = result["motion"]
        p = result["pace"]
        lines += ["## Pace", "",
                  f"- something large moving, cutting or transitioning {int(p['change_share'] * 100)}% of the time; longest settled stretch {p['longest_settle_s']} s",
                  f"- holds of {p['hold_min_s']} s or more: {p['holds']}, covering {int(p['hold_share'] * 100)}% of the video",
                  f"- constant churn: {'yes' if p['churn'] else 'no'}", ""]
        lines += ["## Motion", "",
                  f"- energy per second: {mo['energy_per_second']}",
                  f"- moving {mo['moving_fraction']}, held {mo['held_fraction']}, stepped cadence: {mo['stepped_cadence'] or 'none'}",
                  f"- camera translating in {mo['camera_translation_fraction']} of samples, flashes: {mo['flashes']}", ""]
        a = result["audio"]
        if a:
            lines += ["## Sound", "",
                      f"- tempo about {a['bpm']} BPM, first beat {a['first_beat_s']} s, hard cuts within 60 ms of a beat: {a['changes_on_beat']} (share, and what chance alone would give)",
                      f"- silences at: {a['silences_at_s']}",
                      f"- loudness dB per second: {a['loudness_db_per_second']}", ""]
        lines += ["## Rhythm reading", ""] + [f"- {n}" for n in result["rhythm_reading"]] + [""]
    st = result["style"]
    lines += ["## Style signals", "",
              "| signal | value |", "|:--|--:|"] + [f"| {k} | {v} |" for k, v in st.items()] + [""]
    lines += ["## Style reading", ""] + [f"- {n}" for n in result["style_reading"]] + [""]
    lines += ["## Palette", "", " ".join(f"`{c['hex']}` {int(c['share'] * 100)}%" for c in result["palette"]), ""]
    lines += ["## Sheets", ""] + [f"- `{s}`" for s in result["sheets"]] + ["",
              "Signals are measurements, not a verdict. Read the sheets and name the style yourself."]
    with open(os.path.join(out, "analysis.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--sheet-every", type=float)
    args = ap.parse_args()
    need("ffmpeg")
    need("ffprobe")
    first = args.inputs[0]
    name = os.path.splitext(os.path.basename(first.rstrip("/\\")))[0] or "reference"
    out = args.out or os.path.join("opuscut-ref", name)
    os.makedirs(out, exist_ok=True)
    if first.startswith(("http://", "https://")):
        first = fetch_url(first, out)
        args.inputs = [first]
    images = []
    for p in args.inputs:
        if os.path.isdir(p):
            images += sorted(os.path.join(p, f) for f in os.listdir(p) if os.path.splitext(f)[1].lower() in IMAGE_EXT)
        elif os.path.splitext(p)[1].lower() in IMAGE_EXT:
            images.append(p)
    if os.path.splitext(first)[1].lower() in AUDIO_EXT:
        result = analyze_audio(first)
    elif images:
        result = analyze_images(images, out)
    else:
        result = analyze_video(first, out, args.sheet_every)
    with open(os.path.join(out, "analysis.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    write_md(result, out)
    print(os.path.join(out, "analysis.md"))


if __name__ == "__main__":
    main()
