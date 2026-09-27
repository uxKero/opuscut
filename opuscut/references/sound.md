# Sound

Sound is half of the timing. A video whose sound is chosen and synced feels produced. One with stock effects on every cut feels generated.

## Concept first

Before any cue, write four lines in `video.md`:

- **Material.** What the world sounds like it is made of: wood, glass, paper, rubber, metal, electricity, voice.
- **Key and tempo.** The same grid the picture uses. A minor key reads darker.
- **Motif.** One sound that comes back whenever the visual motif comes back.
- **Arc.** How the sound moves through the video at the picture's pace. It can build to a peak, stay level, or turn quietly.

## Rules

- **One primary sound per moment**, on its verb, with the rest well below it. Not every moment needs a sound.
- **Sound follows the motion.** A sweep matches the speed of the move it accompanies and pans with it across the stereo field. Taking layers out of the mix can mark a comparison as clearly as adding a hit.
- **Size and length follow the picture.** A landing is a short hit. A long move gets a sound that spans it. A transformation gets a phrase that changes.
- **Rests.** A short silence before the peak is the cheapest way to make it hit. Not every cut needs a sound.
- **Sidechain.** Duck the music under hits and voice so they stay clear.
- **Ending.** The last sound decays fully before the last frame.
- **Loudness.** Aim for about -14 LUFS integrated for social platforms, with true peaks under -1 dBTP. `qa.py` measures both.

## Voice

- **Script first.** Write the lines before the picture, short and spoken, one idea per line. Read them against the length: about 2.5 words per second is comfortable.
- **Generate the voice first.** Make one file per line with the user's provider, then run `python <skill>/scripts/voice_envelope.py voice/*.mp3 --fps <fps>`. It gives each line's real duration and speech span, and a mouth value per frame.
- **The voice sets the clock.** Size each beat to its line, and cut or turn in the pauses between lines. The music sits under the voice and ducks while it speaks.
- **A talking character.** Drive the mouth from the `mouth` values: open, close, a few shapes. Add a blink and a small head move on stressed words. Timing matters more than lip accuracy.
- **Captions.** Feeds autoplay muted, so the key words of each line also appear on screen.
- **Keys.** Read the provider key from an environment variable. Never write it into the project, the video folder or `video.md`.

## Sources

- **Synthesis.** `engine/synth.py` has oscillators, envelopes, filters, plucked strings, drum voices, a reverb and a sidechain, all driven by the same `timeline.json`. Build the instruments from the material, not from habit. A marimba is one choice among many.
- **Supplied audio.** The user's music or voice sets the grid. Detect its tempo and phrases with `analyze_reference.py` and cut the picture to them.
- **Generated audio.** Use it only if a generator is already available to the user. Keep the timeline as the authority and place the audio on it.
