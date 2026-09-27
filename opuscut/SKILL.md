---
name: opuscut
description: Direct and render videos made from code (canvas, HTML, Remotion) so that no two look alike. Reads a repo, a brief, a message, or a reference video or images; measures a reference's cutting, motion, sound and drawing style; writes a video.md; renders a frame-exact MP4 with synced sound. Use for promos, launches, explainers, teasers, intros, loops, or "a video like this one".
---

# OPUSCUT

You are directing a short film, not filling a template. Most videos made by code look the same because the model reaches for the same moves every time. This skill exists to make each video look like it could only belong to its subject.

Paths such as `scripts/` and `engine/` are inside this skill's folder. Dependencies: Python with numpy, scipy, Pillow and playwright (with Chromium), plus ffmpeg. See `requirements.txt`.

## Priority order

When two goals pull in different directions, the higher one wins:

1. **Truth.** Every claim, name and number on screen comes from the user or the source. Show the product's real material before drawing a stand-in for it. Invent visuals only where no real material exists, and never invent facts.
2. **Concept.** One idea only this subject could have.
3. **Legibility.** Every word and action reads at playback speed.
4. **Craft.** Motion, timing and sound that feel intentional.
5. **Novelty.** Different from the previous videos in this project.

## Budget

A short video should take one pass of a few minutes, not a long session. Aim for about 20 tool calls from brief to MP4. Every call rereads the whole conversation, so the number of calls costs more than the length of any file. The tools exist to do in one call what would otherwise take several:

- `new_video.py <folder> --size --bpm --beats --fonts "Family;Family:400,700"` creates the folder and downloads the fonts from Google Fonts. Do not search the repo or the web for font files.
- `render.py --beats` gives one contact sheet for the whole video.
- `render.py` renders the video, mixes the sound at -14 LUFS, runs QA and measures the edit, all in one call. Do not run ffmpeg, qa.py or the analyzer yourself after it.

- Batch the calls that do not depend on each other into one message. Read all the files you need together, and apply all the fixes from one review in one script or one batch of edits.
- Load a reference file only when its step needs it. `styles.md` is needed when the style is open or there is a reference. `canvas.md` has the full engine API, so do not open the engine files.
- In a repo, read at most about six files in one batch: the README, the design tokens or global styles, the logo, and one real piece of content such as data, copy or a screenshot. Do not survey the codebase.
- Write `video.md` short: a line per field and a line per beat.
- Write `index.html` and `sound.py` in one pass each. Never read them back to check them.
- Look at one contact sheet of beats and fix everything it shows in a single batch of edits. Then do one full render. Open a single frame only for a problem the sheet cannot show.
- Draft at 30 fps with light motion blur. Raise to 60 fps only if the user asks or fast motion needs it.
- If a render breaks, read the error rather than rendering again blindly.

## 1. Read what you were given

Work out which input you have. There may be more than one.

- **A repo or a brief.** Read the README, the docs, the UI, the copy and the assets. Write down the facts with their sources. Also note the product's **material** (what it touches: paper, code, food, maps, money), its **place** (where the user is when it matters) and its **proof** (what a viewer must see to believe it).
- **Inventory the real material.** Check `package.json` for renderers (three, pixi, phaser, babylon, p5, lottie, a game engine) and look for folders of models, sprites, screenshots and images. List what the product already has to show: its own world, characters, logo, UI screens and real content. A redrawn copy of a product's own world always looks worse than the original and breaks truth.
- **A message only.** Ask what is missing, at most five questions in one turn, each with the default you would choose. Skip anything the message already answers. If the user says "you decide", decide and say what you decided.
  1. What the video is for, and where it plays: platform, aspect ratio, length.
  2. The one thing a viewer should remember.
  3. The drawing style, or a reference, or "surprise me".
  4. The pace: contemplative, measured, flowing, lively or frantic; one continuous take or a cut edit.
  5. The sound: music and effects only, a voiceover, or a character who talks. A voice needs a text-to-speech service the user can reach, such as ElevenLabs or another provider with an API, and their key. Ask which one, and keep the key in an environment variable, never in a file or a log.
- **A reference** (a video, images, or a URL). Measure it before you describe it:
  `python <skill>/scripts/analyze_reference.py <file|folder|url> --out opuscut-ref/<name>`
  Then read `analysis.md` and both contact sheets. Say what the reference lends, choosing from structure, rhythm, style and sound, and what the user wants to keep. By default a reference video lends structure and rhythm as well as look. Test it this way: if swapping in a different reference would change only the colors and the copy, the reading is too shallow.

## 2. Find the style

**The product's own world comes first.** When the product has a world of its own, such as a 3D scene, characters, a game or a distinctive UI, the video is built from it: capture it, and do not replace it or redraw it. Rendering and space then come from the product. The directions vary on everything you direct on top of it: the story, which moments are shown, the camera, the edit, the type, a texture or overlay, and the sound.

The style is the decision that most separates one video from another. Describe it on the axes in [references/styles.md](references/styles.md): rendering, space, motion character, edit grammar, texture, type role and color key. A label such as "cartoon" or "minimal" is not a style.

- **The user named a style, or a reference shows one.** Place it on the axes. Name its signature traits and what would break it.
- **The user brings a direction.** Their direction wins, in their words or with their instructions, even when it goes against a principle in this skill. Build it as well as it can be built.
- **The direction is open.** Offer directions, with no fixed number: as many as are genuinely different, each in one line that covers its concept, style and pace. Let the user pick one, combine several, or write their own. If they asked you not to ask, choose one and say why in a line. Directions come from the material, place or proof, never from the product's category, and they differ in pace as much as in look. Your first idea is usually the stock one, so check it against the habits below.
- **History and taste.** Read `.opuscut/history.md` and `.opuscut/taste.md` in the project if they exist. History says what was already made, so do not repeat a previous video's combination of axes, palette or structure unless the user asks for continuity. Taste says what this user liked and disliked, and it outranks this skill's defaults. After each render, add an entry to the history. Whenever the user reacts to a video, add what they liked or disliked to the taste file, with the reason in their words: "liked the cut on the drop", "no nonstop fast cuts", "footage looked soft".

Blend at most two styles, and let one lead.

## 3. Write video.md

**The idea first.** A video with sense can be told in one sentence and runs on a device: a mechanism such as a transformation, a countdown into a reveal, a before and after, a point of view, a change of scale, a character who carries the viewer through, or one object that travels through the whole film. The device comes from a fact about the product, not from a list, and the video needs a turn, not only a sequence. Answer these while writing `video.md`, not as an extra pass:

- Would the video still work with a competitor's name on it? Then it is generic.
- Does every beat serve the one idea? Cut the ones that do not.
- Where is the turn?
- Does the first frame hook, and does the last one stay?

Before any code, write `video.md` in the video's folder, following [references/video-md.md](references/video-md.md). It holds the concept, the style axes, the palette with a role for each color, the type, the tempo and the grid, the beat table and the hardest frame. Each row of the beat table names an action and its consequence, a verb, the camera, the exit transition and the sound. A beat that has no verb is not designed yet.

## 4. Rhythm

Pace is a choice, not a default. Scenes that change fast from start to end are the most used concept in videos made by code, and repeating it is exactly the sameness this skill exists to avoid. Use it only when the subject and the user call for frantic, and say why in `video.md`. A calm video built on one long take is just as valid. Take the pace from the subject, the concept, the user and the reference. [references/pacing.md](references/pacing.md) covers the range of paces, shot lengths, the shape of the whole, direction of travel and choosing transitions by what they mean.

## 5. Build

Choose the engine that fits what the user already has:

- **Deterministic canvas**, the default. Run `python <skill>/scripts/new_video.py <folder> --size WxH --bpm N --beats N --fonts "..."` and follow [references/canvas.md](references/canvas.md). It lists the whole engine API, so you do not need to open the engine files.
- **Plates from the product itself.** When the product renders its own world, such as a three.js scene, a game, an animated UI or a web page, capture it with `python <skill>/scripts/capture.py`. It runs the product's own code under a virtual clock and saves exact frames that the canvas engine composites under your type and effects. See "Plates" in `canvas.md`.
- **Remotion**, when the project already uses it or the video is built mostly from real footage.
- **Blender, Higgsfield or other generators**, only if their MCP or skill is already available. They add 3D plates or organic footage that get composited into the same timeline. Never make them a requirement. See [references/other-engines.md](references/other-engines.md).

The engine contract, whichever engine you use:

- `renderFrame(n)` is pure: the same frame number always produces the same pixels. Any randomness is seeded.
- One timeline, in beats, drives the picture, the sound and any generated plate.
- Text is drawn in code. Image and video models never write the words.
- Titles and numbers are drawn on a sharp layer that sits above motion blur and grain.

Sound follows [references/sound.md](references/sound.md).

## 6. Prove it, then render

1. Build the whole video, then run `python render.py --beats` and read the one contact sheet. If the hardest frame is doubtful, render just that frame and open it.
2. On the sheet, check for collisions, clipping, contrast, empty or repeated scenes, and anything that contradicts the facts. Fix it all in one round of edits.
3. Write `sound.py`, then run `python sound.py && python render.py`. It prints the QA result and a measure of your own edit. Fix only a QA failure. If the measure contradicts `video.md` (the plan says holds and bursts but the spread is 3x), say so in your summary instead of starting another round.

Deliver the MP4, `video.md` and the contact sheet, each with its path. Say what you could not check. A contact sheet does not show motion at speed, and loudness numbers do not mean the mix was heard, so ask the user to watch and listen for those.

## Hard limits

- Text holds on screen for at least one second per three words, and body text is never smaller than about 2.5% of the frame height.
- Keep text inside the platform's safe area. Vertical feeds cover the bottom 20% and the right edge.
- Feeds autoplay muted, so the on-screen words and images carry the message on their own. Sound adds to the video, and nothing depends on it.
- No more than three full-frame flashes in any one second.
- Nothing clipped, no missing fonts, no black frames or frozen frames the plan did not ask for.
- The sound resolves before the last frame.

## Habits that make code videos look generated

Each habit below is allowed only with a reason that belongs to this video.

| Habit | When it is justified |
|:--|:--|
| Fast cuts, a new scene every bar and nothing ever still | When the pace was chosen as frantic for this subject. It is not a default. |
| A running timer, timecode, frame counter or REC badge in a corner | When the subject is literally a recording or a clock. Otherwise it is decoration pretending to be content. |
| Every element fades in while sliding up | Never as the default. Pick a verb for each element. |
| Every scene lasts the same time | When the concept is a strict metronome or a list. |
| A title at the top center of every scene | When it is a chapter system the concept needs. |
| Glow, grain, ghost text and drifting particles in every scene | When the medium really has them: film, print, space. |
| Near-black with neon cyan, cream with terracotta, a purple-to-blue gradient | When they come from the brand or from the subject's material. |
| The logo in the first seconds | When the logo is the subject. |
| Constant motion with no holds | When the subject is itself frantic. Stillness gives motion its weight. |
| Overshoot bounce on everything | When the world is made of rubber. |
| A whoosh on every cut | Almost never. Silence is also a cut. |
| A particle explosion that forms the logo | When particles belong to the concept, not only to the ending. |
| One kinetic word per beat | When the video is about the words. |
| An invented dashboard or generic UI | Never. Show the real interface, or the product's physical world. |
| A slow push-in on every shot | When the concept is intimacy or tension. |
| Symmetric, centered compositions in every scene | When stillness or ceremony is the point. |
