# Other engines

The canvas engine covers most videos. Use these only when the user already has them or the material needs them, and keep `video.md` and the beat timeline as the authority in every case.

## Remotion

Use it when the project already uses Remotion, or when the video is built mostly from real footage, screen recordings or existing React components.

- Use `useCurrentFrame()` and `interpolate` for everything. CSS animations and timers do not render deterministically.
- Convert beats to frames in one place, and read the timeline from a JSON file shared with the sound script.
- Use `OffthreadVideo` for footage, and normalize variable frame rate recordings to a constant rate with ffmpeg first.
- Everything in this skill still applies: style axes, pacing, the habits table and QA.

## Product UI in React

When the video shows an interface, build it as a real web page instead of drawing it on the canvas. Real components with layered shadows, borders, blur, tooltips and a real chart library (Recharts, visx or ECharts) read as a product. Flat canvas shapes read as a mockup. If the project has its own components, import them.

- **Time drives everything.** Keep one `t` in seconds, updated in a `requestAnimationFrame` loop with `flushSync(() => setT(performance.now() / 1000))`, and derive every value from it: count-ups, chart reveals, hovers, clicks, theme changes and the camera. Turn off the library's own animations (`isAnimationActive={false}` in Recharts) and animate the data or a clip path yourself.
- **Camera.** Wrap the layout in one element with a CSS 3D transform: translate, scale and a few degrees of rotation, interpolated between shots.
- **Preview.** Read `?t=` from the URL as an offset, and check single frames with `capture.py "index.html?t=6.2" --seconds 0.034` before capturing the whole video.
- **Capture.** Use `capture.py` for the full length. Then encode the frames with ffmpeg, mix in the sound with `loudnorm`, fade out the tail, and run `qa.py`.

## Blender

When a Blender MCP or a Blender skill is available, Blender can render what the canvas cannot fake well: real lighting, materials, product turntables, complex 3D dioramas.

- Render plates, not the whole video. Output image sequences with alpha, at the video's frame rate, timed in beats from the same timeline.
- Composite the plates in the canvas engine or in Remotion, and draw all text in code above them.
- Lock the camera and the lighting per shot, and render a single test frame before the whole sequence.

## Generative video and images

When the user already has a generator available, such as the Higgsfield CLI or skills, an image model through OpenRouter, or another image or video model, it can supply organic footage, textures, backgrounds or characters.

Illustrated characters and painted worlds drawn with canvas paths look crude next to real illustration. When a style needs them (anime, painted, character-led) and the product has no art of its own, generate a small set and let the code do the edit, camera, cuts, type, UI and sound:

- **Few images, one style key.** Usually two or three backgrounds and two or three poses of the same character. Write one style paragraph and reuse it in every prompt, and ask for no text in the image.
- **Consistency.** Generate the first character image, then pass it as a reference image for the other poses.
- **Cutouts.** Generate characters on a flat pure chroma green (#00FF00) and cut them out with `python <skill>/scripts/key_green.py <files> --out <video>/assets/art`.
- **Resolution.** Generated images are often around 1280 px wide. Enlarge backgrounds once with a high-quality filter, and draw characters at or below their native size.
- **Cost.** Say the cost per image before generating a batch, and check a single image before generating the rest.

- Generate plates, textures and backgrounds, never words: models misspell and mirror lettering. Draw all text in code.
- Keep one style key for every generation so the plates match each other.
- Test with a still or a short clip before paying for a long one, and fix the scale with a reference object in the frame.
- Place every clip on the beat timeline. The generator's timing never decides the edit.

## Manim, Motion Canvas and others

These fit mathematical or diagram-heavy explainers. The same rules apply: one timeline, text in code where the tool allows it, and the QA pass on the final MP4.
