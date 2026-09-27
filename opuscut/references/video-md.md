# video.md

`video.md` is the plan the build follows and the record that revisions come back to. Write it before any code and update it when the direction changes. Keep each field to a line or two.

## Sections

```markdown
# <title>

## Brief
- For: <purpose, audience>
- Plays on: <platform>, <width>x<height>, <fps> fps, <seconds> s
- Remember: <the one thing a viewer should keep>
- Facts: <each claim with its source>
- Invented: <every visual, sample datum or asset you made up>

## Reference
- Source: <path or none>
- Lends: <structure / rhythm / style / sound, and what exactly>
- Measured: <shots, spread, cuts per 5 s, tempo, silences, key style signals>

## Idea
- One sentence: <the video, told in one line>
- Device: <the mechanism, and the product fact it comes from>
- Turn: <where it turns>

## Direction
- Offered: <each direction in one line: concept, style and pace>, or "brought by the user"
- Chosen: <which one, or the user's own, and why>

## Style
- Rendering: <value>
- Space: <value>
- Motion: <value>
- Edit: <value>
- Texture: <value or none, and the medium it comes from>
- Type role: <value>, <families and why>
- Color key: <light/mid/dark, saturation, contrast>
- Palette: ground <hex>, ink <hex>, accent <hex>, signal <hex>, ...
- Signature traits: <the few that make it this video>
- Breaks if: <what must not happen>

## Rhythm
- Pace: <contemplative / measured / flowing / lively / frantic, or a planned change between them>
- Tempo: <bpm>, <bars>, total <beats>
- Shape: <opening, turns or peak, rests, ending, and where each lands>
- Shots: <how many, and the longest hold>; spread only if it is a cut edit
- Current: <dominant direction>, reserved: <direction = meaning>

## Beats
| Beat | Time | Action and consequence | Verb | Camera | Out | Sound |
|--:|:--|:--|:--|:--|:--|:--|

## Hardest frame
<beat and why; what it must prove>

## Sound
- Concept: <material, key, motif, arc>
- Cues: <the primary sound of each beat>
```

## taste.md

`.opuscut/taste.md` at the project root holds what this user likes and dislikes, one line each, with the reason in their words and the date. Add a line whenever they react to a video. Read it before planning the next one.

```markdown
- 2026-09-26 liked: the reveal landing exactly on the music drop
- 2026-09-26 disliked: fast cuts with no pause from start to end
- 2026-09-26 disliked: footage enlarged until it looked soft
```

## history.md

After each render, append one entry to `.opuscut/history.md` at the project root, so the next video can avoid repeating it:

```markdown
## <date> <title>
- Axes: <rendering / space / motion / edit / texture / type role / key>
- Family: <name or blend>
- Palette: <hexes>
- Structure: <beats in one line>
- Pace and tempo: <pace>, <bpm>, <shot count>
- File: <path>
```
