# Canvas engine

The default engine. The browser draws each frame from its number alone, headless Chromium captures the frames and ffmpeg encodes them. Nothing depends on playback, so every render is frame-exact and repeatable.

## Files

`scripts/new_video.py <folder>` copies the engine and sets the format. You get:

| File | Role |
|:--|:--|
| `timeline.json` | The only source of timing, in beats. Picture and sound both read it. |
| `index.html` | `window.renderFrame(n)` with three layers: world, sharp and finish. |
| `render.py` | Test frames, a contact sheet of every beat, range renders and the full render with sound. |
| `synth.py` | Sound primitives. Write a `sound.py` that uses it and outputs `out/sound.wav`. |

Put fonts, images and any libraries in `assets/` and load them locally. The render never touches the network.

## API

You can write `index.html` from this list without reading the template. Keep its `renderFrame`, `preview` and `ready` blocks, and replace the three draw functions.

- **Globals:** `TL` (the timeline), `W`, `H`, `SPB` (seconds per beat), `ctx` (the output canvas).
- **Time helpers:** `seg(b, from, len)` gives 0..1 progress; `lerp(a, b, t)`; `clamp01`; `sceneAt(b)`; `local(b, scene)`.
- **Easing:** `ease.linear`, `inCubic`, `outCubic`, `inOutCubic`, `outExpo`, `inExpo`, `outBack(t, s)`, `inBack(t, s)` and `outElastic`. `spring(dt, amp, freq, damp)` gives a decaying oscillation.
- **Randomness:** `rng(seed)` and `rngFor(key)` both return a function that yields 0..1.
- **Layers:** `layer()` returns a new canvas of W x H.
- **Draw hooks:** `drawWorld(g, b)`, `drawSharp(g, b)` and `drawFinish(g, n, b)`. `b` is time in beats and `n` is the frame number.
- **Before `__ready`:** fonts from `assets/fonts.css` load by themselves. Extend the async `ready` block for images and precomputed geometry.

`synth.py`, used from your `sound.py`:

- **Time:** `at(beat)` converts beats to seconds, `note("A3")` gives a frequency, `SPB`, `LENGTH`.
- **Voices:** `osc(f, sec, shape)` with sine, saw, square or triangle; `sweep(f0, f1, sec)`; `noise(sec, color)` with white, pink or brown; `pluck(f, sec, bright)`; `mallet(f, sec)`; `bell(f, sec)`; `pad([f...], sec, cutoff=)`.
- **Drums and hits:** `kick()`, `snare()`, `clap()`, `hat(open_=)`, `hit(material)` with wood, glass, metal, paper or rubber, and `riser(sec)`.
- **Shaping:** `adsr(sec, a, d, s, r)`, `filt(x, kind, cutoff)` and `reverb(x, seconds, wet)`. `pad` and `reverb` return stereo arrays of shape (n, 2), so multiply an envelope into them as `env[:, None]`.
- **Mix:** `Mix()` with `.add(sig, sec, bus=, pan=, gain=)`, `.duck(bus, by=, depth=)`, `.silence(start_sec, end_sec)` and `.write("out/sound.wav")`. The final render sets the loudness.

If the user supplied music, skip `synth.py`. Set `bpm` from the track's measured tempo, then trim or fade it with ffmpeg into `out/sound.wav`.

## Timeline

- Everything is in beats: scenes, cues, entrances, hits. Seconds are derived from `bpm`.
- `beats` sets the length. `fps`, `width` and `height` set the format. For vertical video, set 1080x1920 and design for the safe area.
- Add whatever the video needs, such as characters, copy, data or cue lists, so the timing never hides inside drawing code.
- `pace` records the pace chosen in `video.md`. The final render warns when the image rarely settles (too much of the time spent in cuts and transitions, or no hold long enough for the video's length) unless the pace was chosen as lively or frantic.
- `hold` quantizes time for stepped styles: `2` animates on twos, `3` on threes.
- `blur.samples` and `blur.shutter` set motion blur. Use 1 sample for pixel art, stepped styles and anything that must stay crisp.

## The three layers

1. **World** (`drawWorld(g, beat)`) is drawn several times per frame at sub-frame times and averaged into motion blur. It must paint every pixel opaque, starting with the background.
2. **Sharp** (`drawSharp(g, beat)`) is drawn once, above the blur: titles, numbers, captions, UI text.
3. **Finish** (`drawFinish(g, n, beat)`) holds texture, grain, vignette and any overlay. Seed its randomness with the frame number so grain moves but stays repeatable.

## Purity

- `renderFrame(n)` must not depend on any earlier frame. Do not carry state between calls.
- Seed all randomness with `rngFor(key)`, where the key is stable, such as a name plus an index.
- Do physics in closed form, or simulate from 0 deterministically and cache the results by frame.
- Build expensive things once before setting `__ready`: sampled text, particle targets, morph shapes, textures, 3D geometry.
- Get fonts with `new_video.py --fonts`, or put woff2 files and their `@font-face` rules in `assets/fonts.css`. The template loads every face before `__ready`, and the render prints a warning if one fails.

## Techniques that lift a video

Treat these as tools, not as a checklist. Use the ones the concept calls for.

- **Hand-built 3D.** A small perspective or isometric projection function is enough for rooms, boxes and cameras without a 3D library.
- **Morphs.** Resample two outlines to the same number of points and interpolate between them. One shape can travel through a whole film.
- **Text as matter.** Sample a word's pixels into points, then scatter, gather, pour or build it.
- **Character life.** Squash and stretch through `spring()`, blinks on a seeded offset, anticipation before a jump, and a reaction after every action.
- **Simple 3D characters.** A few primitives in three.js (a sphere head, small spheres for hair, a capsule body, flat shapes for the face) with soft light read as a designed toy. Run them through one treatment, such as dither or halftone, and they become a signature look. A simple model with a strong treatment beats a detailed model with none.
- **Camera.** Pan, zoom and roll with eased transforms of the whole world. Shake on impact, decaying fast.
- **Masks.** Shaped clips for wipes and reveals: an iris, a shape from the story, a torn edge.
- **Beat response.** A decaying envelope from the kick times drives small pulses in scale, light or position.
- **Depth.** Parallax layers moved at different rates, and focus falloff through blur on distant layers.

## Treatments

Material from different sources (screenshots, renders, footage, generated images) looks like a collage until one treatment runs through all of it. `treat.js` offers `TREAT.dither`, `TREAT.halftone`, `TREAT.duotone` and `TREAT.sketch(g, image, x, y, w, h, options)`. They draw any image, plate or layer through that look. Use a treatment only when the style calls for it, keep one per film, and apply it to the picture, never to the text. `sketch` into the full render is also a transition: a line drawing that fills in.

## Plates

A plate is a sequence of frames from outside the canvas: the product's own 3D scene or app, a Blender render, or generated footage. The engine composites plates under your type, transitions and effects.

- **Capture the product.** `capture.py` loads a page, replaces `requestAnimationFrame`, `performance.now`, `Date` and timers with a virtual clock, and advances it exactly one frame at a time, so the product's own animation renders frame-exact:
  `python <skill>/scripts/capture.py page.html --out <video>/plates/<id> --seconds S --fps F --size WxH --serve <repo>/public --mount src=<repo>/src --mount node_modules=<repo>/node_modules --wait "window.listo === true" --actions actions.json`
- **A thin page.** When the product is a framework app, do not boot the whole app. Write a small HTML page that imports the product's own rendering module through an import map (for example `"three": "/node_modules/three/build/three.module.js"`), sets up the scene with real data, and drives it from `requestAnimationFrame`. Set `window.listo = true` once it has loaded.
- **Direct the plate.** `actions.json` lists `{"at": seconds, "js": "..."}` calls into the product's own API: move the camera, focus a room, make a character speak, change the time of day. Capture every shot or camera move you need as its own plate.
- **In the timeline.** `"plates": [{"id": "house", "dir": "plates/house", "from": <beat>}]`. In `drawWorld`, `plate('house')` returns the current frame's image or `null`. Draw it like any image, then scale, crop, mask or grade it.
- **Cost.** Capture takes about 0.2 s per frame on a GPU. Capture at the video's fps and only the seconds you use. Check one frame before capturing a long plate.

## Footage quality

Recorded footage loses quality at every resize and every compression, so treat it carefully:

- **Scale once.** `plate_from_video.py` keeps the source's own resolution, and the canvas does the one resize.
- **Do not enlarge past the source.** A plate drawn larger than its native pixels goes soft. At 1.3x it shows, and past 2x it looks broken. The script prints how much a plate must be enlarged to fill the frame. When that number is high, show the footage smaller (inside a frame, a device or a card), crop less, or ask the user for a higher resolution recording. That means 1080p or more, and 1440p or 4K if the video will zoom in.
- **Zoom within the budget.** A slow push-in multiplies the enlargement. Keep the whole move inside what the source can hold, and cut to a tighter crop of a sharper source rather than zooming a wide shot a long way.
- **Near-lossless in between.** Plates are written at maximum JPG quality, or as PNG with `--png`. Frames leave the browser at 99%, and only the final encode is lossy.
- **Name it.** If the only footage available is small, say in the summary that it limits sharpness, and what recording would fix it.

## Libraries

Anything that runs in the browser works if it is loaded from `assets/` and seeks deterministically, for example an easing library, three.js, d3 or opentype.js. For WebGL, create the context with `preserveDrawingBuffer: true` and render synchronously inside `renderFrame`.

## Working loop

1. Write `timeline.json` and `index.html` for the whole video.
2. `python render.py --beats` for one frame per beat in `out/beats.png`. Read that one sheet and fix everything it shows in a single round.
3. `python render.py --frames <n>` only for a problem the sheet cannot show.
4. Write `sound.py`, then run `python sound.py && python render.py`. The render mixes the sound at -14 LUFS, runs QA and prints a measure of the edit.
6. To preview in a browser, serve the folder (`python -m http.server`) and open `index.html?play`. Space pauses, the arrow keys step one frame, and Shift steps one second.
