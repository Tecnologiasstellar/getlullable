# Website asset manifest

Every image the public site loads, where it came from, and whether it is cleared
to ship. Nothing on the site may be a drawing of a screen we intend to build —
if an asset is not on this list with status `APPROVED`, it does not go on a page.

Source workspace for all product assets:
`~/developer/lullable-ios/` (read-only reference — the website
task never edits the app).

Total weight of `assets/`: **~300 KB across 16 files**, plus 171 KB of
self-hosted fonts in `fonts/` (see [fonts/README.md](../fonts/README.md)).

---

## App screens — `assets/app/`

All four are crops of the **approved App Store screenshot set v2**
(`# Getlullable App Store Screenshots_v2,0.zip` → `export/appstore-iphone-6.9/`,
exported 2026-08-24). The crop takes the device out of the marketing board and
drops the headline type; **nothing inside the screen was repainted, recoloured or
retouched.** Bezel, Dynamic Island, status bar (11:41 / 7:02) and corner radius
are the board's own and identical across all four, so no two iPhone generations
are mixed. Corners are masked to alpha at 12.5% of width so the device sits on
the page ground rather than on a rectangle.

| File | Screen | Source board | Px | Ratio | Size | Used on | Status |
|---|---|---|---|---|---|---|---|
| `screen-tonight.webp` | Tonight — the story chosen for the night | `lullable-01-deeper-sleep.png` | 780×1721 | 0.453 | 27.3 KB | Hero (LCP), walkthrough step 01 | `APPROVED` |
| `screen-library.webp` | The Sleep Library — browse | `lullable-02-the-sleep-library.png` | 780×1720 | 0.454 | 44.1 KB | Walkthrough step 02 | `APPROVED` |
| `screen-player.webp` | Player, mid-story, timer running | `lullable-03-now-playing.png` | 780×1720 | 0.454 | 34.7 KB | Walkthrough step 03 | `APPROVED` |
| `screen-mornings.webp` | Mornings — the quiet receipt | `lullable-04-wonderful.png` | 780×1721 | 0.453 | 30.1 KB | Walkthrough step 04, Mornings section | `APPROVED` |

Preparation: `PIL`, crop → LANCZOS resize to 780w → rounded-alpha mask → WebP
q86 method 6. Every `<img>` carries explicit `width`/`height`, so none of them
can shift layout. The hero copy is `fetchpriority="high"` and preloaded; the
other three are `loading="lazy"`.

**Rights:** own work, produced for Lullable's own App Store listing.

> ⚠️ These are **authored App Store screens**, not raw device captures. They are
> the product's approved public representation and the UI in them is the shipping
> UI, but if the app's chrome changes before launch these must be re-exported
> from the same board and re-cropped. The crop boxes are recorded in
> `docs/MISSING_WEBSITE_ASSETS.md` so the step is repeatable.

## Story artwork — `assets/art/`

Durations and genres throughout come from `lullable_audio/Stories/<slug>/story.yaml`,
which supersedes the app's older `Resources/catalog.json` where the two differ.

Lullable's proprietary artwork system, **"Echo Contours"**: 3–5 strokes that
repeat thinner, darker and further along one direction — a voice trailing off.
Geometry ground truth copied verbatim from
`lullable_ios/design_handoff_story_artwork/svg/`. The site inlines the same path
data (so it inherits no extra request) and drops the animated "mote", which the
handoff already specifies as hidden under Reduce Motion.

| File | Story | In app catalogue | Used on | Status |
|---|---|---|---|---|
| `the-rings-of-saturn.svg` | The Rings of Saturn — 38 min, Cosmic Journeys, free | yes | Story-world gallery | `APPROVED` |
| `the-bakery-before-dawn.svg` | The Bakery Before Dawn — 40 min, Cozy Tales, free | yes | Story-world gallery | `APPROVED` |
| `the-deep-ocean-trenches.svg` | The Deep Ocean Trenches — 40 min, Gentle Nature | yes | Story-world gallery | `APPROVED` |
| `aristotle-the-greatest-philosopher.svg` | Aristotle, the Greatest Philosopher — 40 min, Ancient Worlds, free | yes | Story-world gallery | `APPROVED` |

**Aristotle's artwork was drawn for this pass, and its geometry is derived rather
than invented.** The column is the story's own canonical `sigilPaths` from
`lullable_audio/Stories/aristotle-the-greatest-philosopher/story.yaml`; the Echo
Contours law then repeats it along one direction, and the direction is the walk —
Aristotle taught while walking, so the echo turns his single column into the
colonnade he walked. Weights, ramp, dissolving ground line and the single true
figure (`384 BC`) follow the published kit exactly. A different designer redrawing
it should start from the same sigil.

The files themselves are kept next to the inlined copies so the geometry has one
checkable source. The same grammar is redrawn (not copied) as the hero horizon,
the section rule, the sample player's progress track and the mechanism diagram —
those are site compositions in the app's system, not story artworks.

**Rights:** own work (Lullable design handoff, 2026-08).

## Brand — `assets/brand/`

| File | What | Source | Used on | Status |
|---|---|---|---|---|
| `mark-128.webp` | The mascot-and-horizon mark, night version | `export 5/instagram-logo/lullable-logo-night-1080.png` | Header + footer wordmark | `APPROVED` |
| `web/favicon.svg` `web/favicon-32.png` `web/apple-touch-icon.png` `web/icon-192.png` `web/icon-512.png` `web/favicon.ico` | The shipping app-icon favicon set | `lullable_ios/.../BrandAssets/Lullable-AppIcon/Web/` | `<head>` of every page | `APPROVED` |
| `web/site.webmanifest` | PWA manifest | same, **paths and theme colour rewritten** for this site (`#161826`) | `<head>` | `APPROVED` |
| `/favicon.ico` (repo root) | Copy of the above, so the default crawler path 200s | same | root | `APPROVED` |

The wordmark itself is **type, not an image**: lowercase `lullable`, Inter 300,
`letter-spacing: .30em`. The app's handoff calls the tracking the identity and
forbids going below `.28em`; the site follows that rule.

## Audio — `audio/`

| File | What | Status |
|---|---|---|
| `sample-aristotle.mp3` | 3:50 of *Aristotle, the Greatest Philosopher*, **read by Emma from Oxford** — the settling preamble, which ends almost exactly where the story proper begins | `APPROVED` |

**Re-cut on 2026-08-25** from the current production master
(`lullable_audio/Stories/aristotle-the-greatest-philosopher/audio/delivery.m4a`,
`audio-aristotle-en-v2-aac96`) with `ffmpeg -t 230 -ac 1 -b:a 64k`. The previous
file was the v1 ElevenLabs render narrated by "Andrew" — a narrator the app no
longer has, since the episode was re-voiced with Polly Emma on 2026-08-20. A
visitor who liked the sample and then opened the app would have heard a different
person. The old file is in git history if the earlier voice is preferred; it is
one `git checkout` to put back, but the page copy would have to go back with it.

Never autoplays. `preload="none"` — nothing downloads until the visitor presses
play. The last 30 s ramp to silence in JS, mirroring the app's own 10-second
sleep-timer fade. **Caption cues were measured off the file**, not guessed:
`ffmpeg silencedetect` yields the speech segments and the narration text is
distributed across them. Re-derive them if the sample is ever re-cut.

## Share image — `og.png`

Generated by `make-card.py`, re-tokened to Nocturne in this pass. It is the
morning receipt, not a logo: a stranger seeing the link understands the company
before clicking. **The footer line was changed from "Asleep by 11:41pm" to
"Last listened at 11:41pm"** — see `docs/MISSING_WEBSITE_ASSETS.md` § Claims.

1200×630, 80 KB. Per-story cards under `stories/*/og.png` are regenerated by
`build.py` from the same renderer.

---

## Story pages — `catalog/*.md` → `/stories/<slug>/`

Six of the app's ~25 production-verified stories, chosen so the set covers all
four genres and **one story per narrator**, showing the whole voice cast:

| Story | Genre | Narrator | Min | Access |
|---|---|---|---|---|
| Aristotle, the Greatest Philosopher | Ancient Worlds | Emma from Oxford | 40 | free |
| A Roman Bathhouse at Closing Time | Ancient Worlds | Arthur from Ludlow | 39 | premium |
| Floating Through the Pillars of Creation | Cosmic Journeys | Amy from Greenwich | 41 | premium |
| The Slow Life of a Redwood | Gentle Nature | Patrick from Block Island | 41 | premium |
| The Midnight Sleeper Train Across the Alps | Cozy Tales | Niamh from Kinsale | 40 | premium |
| The Midnight Museum Beneath the Sea | Gentle Nature | Brian from St Ives | 20 | premium |

Every field — title, narrator persona, duration, genre, access, cover colours and
sigil paths — is copied from `lullable_audio/Stories/<slug>/story.yaml`, and every
"first minute" excerpt is the real recorded script from `narration.md`. All six
are `workflowStatus: published`, `rights.status: verified`, QA-approved, and
verified in production.

Each page now renders **the app's real cover**: the ground is the app's
`StoryVisualIdentity` radial (`glow` → `base`, centre .5/.16, end radius .62) and
the mark is the story's own `sigilPaths` stroked in `accent` at 2.6 in the
100-unit sigil space. Colours and paths ride in the catalog frontmatter, so
`build.py` stays self-contained and the site never reads the app repo at build
time.

## Deliberately not used

- `lullable_ios/.../Bedtime stories app design/design/screenshots/*.png` — an
  earlier prototype: a four-tab bar (Home/Browse/Library/Profile) that the
  shipping app no longer has, sample user data, and literal `COVER ART`
  placeholder labels. Using them would misrepresent the product.
- `export 4/appstore-set-B-midsentence/` — an alternative App Store set. Same
  quality; not mixed with set v2 so the four screens read as one device and one
  session. Available if set B is preferred; swap all four, never one.
- Any AI-generated or stock imagery. The site's only pictures are the app and
  its own artwork system.
