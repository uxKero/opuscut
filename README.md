<div align="center">

# OPUSCUT

A film director for coding agents.

<a href="https://x.com/uxKero"><img alt="Made by @uxKero" src="https://img.shields.io/badge/MADE%20BY-%40uxKero-000000.svg?style=for-the-badge&logo=x&labelColor=000000"></a> <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/LICENSE-MIT-000000.svg?style=for-the-badge&labelColor=000000"></a> <a href="opuscut/SKILL.md"><img alt="Agent Skills format" src="https://img.shields.io/badge/FORMAT-AGENT%20SKILLS-000000.svg?style=for-the-badge&labelColor=000000"></a> <a href="https://skills.sh/uxkero/opuscut/opuscut"><img alt="Listed on skills.sh" src="https://img.shields.io/badge/SKILLS.SH-LISTED-000000.svg?style=for-the-badge&labelColor=000000"></a>

<br><br>

<img src="assets/cover.jpg" alt="The word OPUSCUT sliced in two, with a strip of film running through the cut" width="100%">

</div>

<br>

Everyone is making promo videos with Opus 5.5, and they all look alike: the same fade-in, a timer in the corner, a cut every two seconds. OpusCut is a skill for that. Give it your repo, a brief or a video you like, and it works out the style and the pace, uses your real app and footage, and remembers what you liked for the next one. Built for Opus 5.5, works with any model that reads skills.

<img src="assets/showcase.jpg" alt="Frames from videos made with OPUSCUT: a sleep dashboard, an anime swordsman in front of the moon, a rain radar map, an isometric house, and a close-up of red eyes" width="100%">

## What is inside

- Asks only what is missing, and lets you bring your own idea.
- 25 styles, from editorial and isometric to anime and product UI.
- A pace picked for the video: calm, measured or fast, never fast by default.
- Uses your app, footage, 3D and logo before drawing anything.
- Reads reference videos: the cuts, the pace, the palette, the drawing style.
- Keeps a note of what you liked in each project.

## Install

```bash
npx skills add uxKero/opuscut
```

Or copy the `opuscut` folder where your agent reads skills, then restart the agent.

| Agent | Personal | Per project |
|:--|:--|:--|
| Codex | `~/.agents/skills/` | `.agents/skills/` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |

```bash
git clone https://github.com/uxKero/opuscut.git
cp -r opuscut/opuscut ~/.agents/skills/
```

It renders on your machine, so it needs Python and [ffmpeg](https://ffmpeg.org). The first time, install the rest:

```bash
pip install -r opuscut/requirements.txt
python -m playwright install chromium
```

<br>

<div align="center">

Made by [@uxKero](https://x.com/uxKero) under the [MIT License](LICENSE).

</div>
