# Styles

A style is a position on seven axes, not a name. Names help you talk about a style. Axes help you recognize one, build it and keep it consistent. Read a reference on every axis before you name it, and describe a new direction on every axis before you build it.

## The axes

Each axis lists how to recognize it in a frame or in motion, and which `analyze_reference.py` signals point to it. Signals suggest; your eyes on the contact sheet decide.

### 1. Rendering: how surfaces are drawn

| Value | Recognize it by | Signals |
|:--|:--|:--|
| Flat fill | Solid shapes with no shading and hard edges | `colors_95` low, `flat_fraction` high |
| Cel shaded | Flat base plus one or two hard shadow tones | Low colors, flat, with shadow shapes that repeat the base hue |
| Soft shaded | Smooth gradients on forms, like airbrush or clay renders | `ramp_fraction` high, colors in the mid range |
| Line art | Strokes carry the form and fills are sparse or absent | `edge_density` high, `flat_fraction` high |
| Inked cartoon | Fills with a dark outline around each shape | `dark_outline_share` high |
| Textured print | Flat inks with grain, misregistration, halftone or paper | Flat, with high `grain` and few colors |
| Painted | Visible brush, uneven edges, color variation inside shapes | Colors high, ramp medium, grain medium |
| Rendered 3D | Lighting, occlusion, specular highlights, depth of field | Ramps high, colors high, soft edges |
| Photographic | Camera noise, real optics, motion blur from a shutter | `colors_95` very high, `flat_fraction` very low |
| Pixel | A visible grid, a tiny palette, no anti-aliasing | Very few colors, `lines_axis` very high, hard steps |

### 2. Space: how depth is built

| Value | Recognize it by |
|:--|:--|
| Frontal plane | Everything faces the camera, with depth only from overlap and scale. `lines_axis` dominates. |
| Layered 2.5D | Flat planes at several depths that move at different speeds under a camera move |
| Isometric or axonometric | Parallel edges that never converge, usually at 30 degrees. `lines_iso` is high. |
| Perspective | Converging lines, a horizon, a real lens |
| Abstract field | No ground or horizon, and shapes float in a graphic space |
| Screen space | UI, the page or the grid is the world |

### 3. Motion character: how things move

| Value | Recognize it by |
|:--|:--|
| Stepped | Drawings held for two or three frames (`stepped_cadence`). Reads handmade, stop motion or anime. |
| Fluid eased | A new pose every frame with smooth easing. Reads digital and polished. |
| Physical | Weight, squash and stretch, overshoot, settle. Things fall and land. |
| Mechanical | Linear moves, hard stops, snapping to a grid, clicking into place |
| Organic | Drift, breathing, noise, morphs, fluids |
| Camera-led | Objects stay still and the camera travels (`camera_translation_fraction` high) |
| Still-led | Long holds broken by sudden changes. Energy comes from the contrast. |

### 4. Edit grammar: how time is cut

| Value | Recognize it by |
|:--|:--|
| Continuous take | One shot or very few cuts. The camera and the objects carry the change. |
| Scene per beat | A change of scene on a musical grid, often through transitions |
| Montage | Many cuts, a wide spread of lengths, bursts and holds |
| Match-cut chain | Each shot ends on the shape that starts the next |
| Morph chain | Shapes transform into each other with no cut at all |

The spread, the cuts per 5 s and the soft transitions in `analysis.md` tell these apart.

### 5. Texture: what sits over the image

None, paper, film grain, halftone, scanlines or CRT, VHS, risograph misregistration, noise, dust and scratches, light leaks. A texture has to belong to a medium. If you cannot name the medium, you do not need the texture.

### 6. Type role: what the words do

| Role | What it looks like |
|:--|:--|
| Absent | The picture carries everything |
| Caption | A small line that supports the picture |
| Headline | Large words that share the frame with the picture |
| Kinetic | The words are the picture: they move, stack and transform |
| Diegetic | Words live inside the world: signs, screens, labels, paper |
| Interface | Real UI text inside a rebuilt product screen |

### 7. Color key

Light, mid or dark key (`luminance`), saturated or muted (`saturation`), high or low contrast (`contrast`), and how many hues carry meaning. Write the palette as roles (ground, ink, accent, signal), never as a mood word.

## Families

The families below are known combinations of axes, useful as shorthand. Each lists its signature, what it needs, and what breaks it. None is a default for any kind of product, and you can blend two when one leads. New combinations are welcome.

**Flat vector explainer.** Flat fill, frontal or layered, fluid or physical, scenes per beat, headline type. Signature: shapes that morph into each other, icons that draw on, mask wipes. Breaks when detailed and flat drawing get mixed, or when the frame fills with too many icons.

**Isometric diorama.** Flat or cel, isometric, physical, continuous take or scenes per beat. Signature: a miniature world that assembles itself, props that drop in with contact shadows, a camera that orbits or pushes into one room. Breaks when perspective sneaks in, when light comes from several directions, or when there are too many props per island.

**Cozy cartoon.** Inked or cel with round characters, any space, physical with squash and stretch, blinks and anticipation. Signature: characters act out the idea and a reaction sells each beat. Breaks when characters only stand and wave, or when their proportions drift between scenes.

**Kinetic typography.** Flat, screen space, mechanical or physical, montage, kinetic type. Signature: words that scale, rotate, stack, invert and cut on the beat. Breaks when a line holds for less time than it takes to read, or when there are more than two type families.

**Swiss editorial grid.** Flat, screen space, mechanical, montage or scenes per beat, headline type. Signature: a strict grid, huge numerals, color blocks that wipe on the downbeat, asymmetric balance. Breaks when anything sits off the grid or gets decoration.

**Brutalist.** Flat or photographic, screen space, mechanical or still-led, hard montage, kinetic type. Signature: raw default type, harsh contrast, visible structure, abrupt cuts. Breaks when it is polished halfway.

**Paper cutout and collage.** Textured print or photographic cutouts, layered 2.5D, stepped, scenes per beat. Signature: shadows under the paper edges, pieces that slide in on strings, torn edges. Breaks with perfectly smooth motion or with no shadows.

**Risograph and print.** Textured print, frontal or layered, stepped or organic, any edit. Signature: two or three ink colors that overprint into a third, misregistration and grain. Breaks with more inks than the concept allows or with clean digital gradients.

**Claymation look.** Soft shaded or rendered, perspective, stepped on twos, physical. Signature: fingerprints, a slight wobble between frames, chunky proportions. Breaks when motion is too smooth.

**Soft 3D toy.** Rendered 3D with rounded forms and gentle light, perspective or isometric, physical. Signature: bevelled toy-like objects, soft shadows, bouncy assembly. Breaks with realistic textures or harsh light.

**Product hero 3D.** Rendered or photographic, perspective, camera-led and still-led, long holds cut on the beat. Signature: slow orbits around the real object, light sweeps, extreme close-ups of materials. Breaks with too many words or with a fake object instead of the real one.

**Low-poly and faceted.** Flat-shaded 3D with visible facets, perspective or isometric, mechanical or physical. Signature: facets that catch a single light, geometry that assembles. Breaks with smooth shading mixed in.

**Pixel art.** Pixel, frontal or side-scrolling layered, stepped, scenes per beat. Signature: a strict grid, limited palette, sprite animation, chiptune. Breaks with sub-pixel motion, rotation or anti-aliasing.

**UI story.** Screen space with the real interface, fluid eased, camera-led pushes into components, interface type. Signature: a cursor with intent, zooms into the component that proves the claim, real data. Breaks with invented dashboards or text too small to read.

**Data story.** Flat, screen space, mechanical, still-led, headline plus labels. Signature: one number per beat, bars and lines that draw in data order, a camera push to the value that matters while the rest dims. Breaks with decorative color or more than one message per chart.

**Line and doodle.** Line art on a plain ground, frontal, stepped or drawn on, morph chain. Signature: strokes that draw themselves, boil (lines that wobble between frames), handwritten type. Breaks with perfect geometric strokes.

**Anime and cel.** Inked cel, perspective with dramatic angles, stepped with fast smears, montage. Signature: speed lines, impact frames, held key poses, backgrounds painted in a different style from the characters. Breaks with even, fluid in-betweens.

**Retro screen.** Pixel or photographic, screen space, mechanical, montage. Signature: scanlines, CRT curvature, VHS tracking, glitch that appears on meaning and not at random. Breaks when glitch is constant.

**Blueprint and technical.** Line art on a solid ground, orthographic or isometric, mechanical and drawn on. Signature: dimension lines, callouts, parts that explode apart and rejoin. Breaks with decorative illustration.

**Halftone comic.** Inked with halftone texture, perspective, stepped, panels as the edit. Signature: panel borders that hold several moments at once, onomatopoeia, dots in the shadows. Breaks with smooth gradients.

**Geometric abstract.** Flat, abstract field, mechanical or organic, morph chain. Signature: primary shapes in a strict set that rearrange to the music, in the Bauhaus tradition or generative. Breaks when figurative elements drift in.

**Liquid and morph.** Soft shaded or flat, abstract field, organic, morph chain. Signature: blobs that merge and split, metaballs, fluid transitions. Breaks with hard cuts.

**Terminal and ASCII.** Text as the image, screen space, mechanical typing, continuous take. Signature: a monospaced grid, a cursor, output that scrolls, art drawn from characters. Breaks with fonts that are not monospaced or with motion that is not on the grid.

**Map and journey.** Flat or textured, top-down or tilted perspective, camera-led, continuous take. Signature: a route that draws itself, the camera flying between places, labels on locations. Breaks with no sense of scale.

**Photo and footage led.** Photographic, perspective, montage, caption or headline type. Signature: real footage cut to the beat, typography layered over the picture, speed ramps. Breaks when motion graphics fight the footage instead of framing it.

## Reading a reference, in order

1. Run the analyzer and open `shots.png` and `timeline.png`.
2. Fill in all seven axes, each with the evidence behind it, a signal or something you can see.
3. Name the family, or say that it is a blend or none.
4. List the signature traits that make it *that* video, and what would break them.
5. Separate what the user wants to take from the rest.
