# Lullable — Site Spec

The page is built. This file records the decisions behind it so the next change
doesn't undo them.

Everything lives in [index.html](index.html): one file, no build step, no
framework, no bundler. `build.py` generates `/sleep/` and `/stories/` from the
same token set but never touches the homepage. When there's a signup flow, a
paywall and a library, it becomes a Next.js app — not before.

**Redesign, 2026-08-25.** The site was an elegant product thesis with a
hand-drawn CSS phone. It is now an app showcase built on the shipping app's own
design system, with four real screens in it. What changed and why is below.

---

## 0. The one rule everything follows

**Nothing on this page should be bright enough to wake someone up** — it is
browsed in bed, in the dark, one-handed, often after a failed attempt at sleep —
**and nothing on this page may be a drawing of a product we have not built.**

The second half is new, and it is the more expensive of the two.

---

## 1. Design system: Nocturne, not Nightfall

The site used to run "Nightfall" (`--ink #0E0F16`, amber `#DFAF83`, iris
`#A79FD9`), imported from a Claude Design token file. **The iOS app has since
shipped a different system, and the app wins.** The app has no amber at all; its
accent is violet and its second colour is a warm cream.

Source of truth, now and going forward:
`lullable_ios/01_iOS_App/SleepStoriesApp/design_handoff_onboarding_flow/README.md`
§ *Design tokens*, mirrored in `SleepStories/DesignSystem/Theme.swift`.

| Token | Value | Role |
|---|---|---|
| `--bg` | `#161826` | The one ground. Every page, every section. |
| `--surface` | `#232532` | The player card, the receipt, the cookie panel. |
| `--raised` | `#1C1E2B` | Inputs. Sits *below* surface in lightness on purpose — raised by border, not brightness. |
| `--cream` | `#ECE4D3` | The wordmark and every primary button's border and label. The brand's second colour. |
| `--text` / `--text-2` | `#E9E9ED` / `#B2B6CA` | Headings / body. |
| `--text-3` | `#8E92A8` | Captions and meta only, **never body copy**. Lightened from the app's `#83879C`, which is AA on `--bg` but 4.28:1 on `--surface`, where this site also uses it. |
| `--accent` | `#9184D9` | **A line, a border and a glow. Never a flood.** |
| `--accent-lt` | `#B5ABFC` | Eyebrows, step numbers, footnote markers. |
| `--ramp-700/800/900` | `#5D5294` `#423A6A` `#2B2741` | The echo ramp — see §2. |
| `--glow` | `#262A60` | The one sectional wash (hero, final CTA). |
| `--sand` | `#C9B491` | One warm note, sampled from the app's Mornings horizon. Used once, on the receipt's wordmark. |
| `--line` | `rgba(233,233,237,.14)` | Every hairline. |

Measured contrast on the grounds they are actually used on: `--text` 14.5,
`--text-2` 8.8/7.6, `--text-3` 5.7/4.9/5.4, `--cream` 13.9, `--accent-lt` 8.6,
`--accent` 5.5. All AA for normal text.

**Buttons.** The app has exactly one button shape and the site adopted it:
transparent fill, 1.5 px cream border, cream 16 px/500 label, radius 14, height
52–54. Pressed fills `rgba(236,228,211,.10)`.

The app also keeps exactly **one filled button**, for the one action that matters
(Continue with Apple). The site spends that same allowance on the three app CTAs —
hero, mid-page band, and the join form — which carry `.solid`: cream fill, ink
label. Header and secondary actions stay outlined, so there is one obvious thing
to press per screenful and it is always the same thing. A violet-filled button
would break the never-flood rule; there are none.

## 2. The one motif: Echo Contours

The app's story-artwork system (`lullable_ios/design_handoff_story_artwork/`):
**3–5 strokes that repeat thinner, darker and further along one direction — a
voice trailing off.** Weights `3.5 / 2.6 / 2.0 / 1.6 / 1.3`, round caps, ramp
`accent → 700 → 800 → 800@65% → 900`, ends dissolving over the outer 23%.

It is Lullable's, it means something, and it is the site's only decorative idea.
It appears five times and nowhere else:

1. **Hero backdrop** — the horizon form, arcs bleeding off the bottom, masked to
   fade in from the top. Same grammar as the app icon.
2. **Section rule** — three lines dissolving at both ends, in place of an `<hr>`.
3. **The descent** — a full-bleed fall from left to right after the "your brain
   isn't broken" statement.
4. **Sample player progress** — the track is three ramp lines; the fill is the
   same three lines one step brighter. Playback literally redraws the motif.
5. **Mechanism diagram** — the same descent, this time with axes and labels:
   racing thoughts → gentle attention → reduced effort → sleep.

Four real story artworks are inlined in the story-world gallery. Three are
verbatim from the handoff SVGs; Aristotle's was drawn in this pass by echoing his
own canonical `sigilPaths` along one direction — the walk. Derived, not invented. **The animated "mote" is not used on the web** — the handoff
already specifies it hidden under Reduce Motion, and a looping dot on a marketing
page is a different thing from a looping dot on a player you are falling asleep
to.

No blobs, no aurora, no starfield, no glassmorphism, no gradient headings, no
icon set. The page's only images are the app and the app's own artwork.

## 3. Typography

**Self-hosted, no third party.** The latin-subset woff2 files live in `fonts/`
and the `@font-face` rules are inline in `index.html` and in `build.py`'s `CSS`.
The page makes **zero requests to any other host**, which is both the honest
reading of what `/privacy/` promises and the safe reading of GDPR. Do not put a
`<link>` to fonts.googleapis.com back. Provenance, licence and the re-fetch
recipe: [fonts/README.md](fonts/README.md).

Two faces, with jobs that never overlap:

- **Inter** (300–600, one variable file) — the app's UI face. Headlines, navigation,
  labels, product chrome, the wordmark, the diagram.
- **Newsreader** — the *story* voice, and only that: the italic phrase inside
  each headline (`em.voice`), transcript fragments, story titles in the gallery,
  the player's captions, the receipt's quote.

That split is the point. The sans is the product talking; the serif is what the
product reads to you. Three local woff2 files cover both, `font-display:swap`;
the homepage preloads Inter and Newsreader italic, the generated pages preload
Inter and Newsreader roman.

**The wordmark is type, not a logo lockup:** lowercase `lullable`, weight 300,
`letter-spacing: .30em`. The handoff calls the tracking the identity and forbids
going below `.28em`. The mascot mark sits beside it at 30 px.

Scale: display `clamp(2.35rem, 4.7vw, 4.5rem)`, section `clamp(2rem, 4vw,
3.6rem)`, lead `clamp(1.06rem, 1.25vw, 1.28rem)`, labels ≥ 12 px always.

## 4. Page structure — product → problem → mechanism → experience → proof → action

| # | Section | Does one job |
|---|---|---|
| A | Header | Sticky, transparent at rest, gains a blurred surface past 24 px. |
| B | **Hero** | Positioning, one action, and a **real Tonight screen** big enough to read. LCP image, preloaded, `fetchpriority=high`. |
| C | Product-truth strip | Four things the app does, all verified on a device. **Not** a trust-logo row — there is nothing verified to put in one. |
| D | The statement | *Your brain isn't broken — it's just curious.* Asymmetric, left, huge, then the descent. |
| E | **A night with Lullable** | Four steps, four real screens. Sticky figure on the right, narrative on the left. |
| F | Story world | The Echo Contours grammar and four real artworks, each a real catalogue story; the four real genres. |
| G | Sample | 3:50 of the real Aristotle recording. The last 30 s fade to silence. |
| H | Mechanism | One argument, a labelled descent diagram, three numbered sources, the disclaimer. |
| I | Spectrum | Too empty → too demanding → **just enough** → too interesting. One instrument, not four cards. |
| J | Mornings | The real receipt, in the app's own words. |
| — | **CTA band** | One line, one filled button, sitting between the walkthrough and the story world. The page's mid-point conversion moment. |
| K | Join | One field. Says plainly that it is both the waitlist and the letter. |
| L | Footer | Four columns, legal intact. |

Rhythm is deliberately unequal: `.s-lg` and `.s-md` differ, not every section is
centred, not every surface has the same radius, and the gallery, spectrum and
proof strip each use a different composition. **If a future change makes three
sections look like each other, it is the wrong change.**

### The walkthrough, specifically

`position: sticky` on the figure *inside each step*, not one JS-driven stage.
The device holds while its step's copy scrolls, then the next step's device
arrives. No scroll-jacking, no absolute positioning, no duplicated images, and on
mobile it degrades to exactly what mobile wants — one step, then its screen.
Steps fade in via `IntersectionObserver`; under `prefers-reduced-motion` they are
simply visible.

The figure is always on the **same side** on desktop. An earlier version
alternated; it read as a pile of phones.

## 5. The sample player

| | |
|---|---|
| Source | `audio/sample-aristotle.mp3` — 3:50, the opening of the app's one production story |
| Preload | `none`. Nothing downloads until pressed. |
| Controls | Play/pause, elapsed, remaining, a non-interactive progress line. No scrubbing — scrubbing implies there's a good bit. |
| Fade | The last 30 s ramp to silence, squared curve, in JS (`FADE_SECONDS`). The widget's thesis, stated in audio. |
| Captions | Timed serif lines under the player, so a sound-off visitor still gets the sensation. |
| Failure | If the file 404s the player says so and points at the letter. It never fakes success. |
| Hero link | *"Play the four-minute sample ↓"* scrolls **and** starts playback — the click is the user gesture, so it is allowed to. |
| Events | `sample_play`, `sample_finished`, `sample_missing` |

**The number that matters: % of visitors who press play.** Below 15%, the
headline is wrong — not the audio.

## 5b. Story pages

Six of the app's ~25 production-verified stories, one per narrator, covering all
four genres. Every field in `catalog/*.md` — title, narrator persona, duration,
genre, access, cover colours, sigil paths — is copied from
`lullable_audio/Stories/<slug>/story.yaml`, and every "first minute" is the real
recorded script. **If the manifest and the site disagree, the manifest wins.**

Each page renders the app's real cover, rebuilt in SVG from
`StoryVisualIdentity`: a radial ground `glow → base` (centre .5/.16, end radius
.62) with the story's own `sigilPaths` stroked in `accent` at 2.6 in the 100-unit
sigil space. A story missing either the colour pair or the paths falls back to a
plain ground — never to an invented mark, which is the choice the app makes for
the same reason.

Adding one of the other ~19 is `python3 build.py story <slug>`, then copy the
fields across. `vercel.json` holds 301s for the six invented stories this
replaced.

## 6. Claims

The page may state a product fact only if it is checkable in the app repo.
Everything currently unverifiable — App Store availability, price, trial terms,
ratings, testimonials, catalogue size — is omitted, and listed in
[docs/MISSING_WEBSITE_ASSETS.md](docs/MISSING_WEBSITE_ASSETS.md).

Two corrections made in this pass are worth remembering:

- **"Asleep by 11:41pm" is gone**, from the page and from `make-card.py`. The app
  records a last-listened position; it does not detect sleep onset. The line is
  now *"Last listened at 11:41 pm."*
- **The free-trial line is gone.** No trial length or price is verified anywhere
  the website can check it.

The research section still separates *research on the mechanism* from *proof
about the product*, and still says so out loud. Do not remove that sentence to
improve conversion.

## 7. Consent, motion, accessibility

- **Consent** ([consent.js](consent.js)): unchanged in behaviour, restyled to
  Nocturne and moved to a 25 rem bottom-right panel that appears after 1.2 s.
  Global Privacy Control is honoured silently. Nothing optional loads before an
  answer, so the delay costs nothing and lets the hero land first. Accept and
  Decline are the same size, the same shape and equally legible.
- **Motion**: product transitions 500–800 ms, micro-interactions 150–250 ms,
  reveals only on the four walkthrough steps, no parallax, no autoplay, no
  scroll-jacking. Under `prefers-reduced-motion` every transition and animation
  is off, smooth scrolling is off, and all content is present — verified.
- **Accessibility**: one `<h1>`, ordered headings, landmarks, a skip link, 44 px
  targets on every control, visible focus rings on `--accent-lt`, alt text that
  describes the *product state* rather than the phone, `aria-pressed` and a
  changing `aria-label` on the play button, `aria-live` form status, `Escape`
  closes the mobile menu. Links carry an underline, never colour alone.
- **Responsive**: verified at 1440, 1280, 1024, 768, 430, 390, 375 and 320. No
  horizontal overflow at any of them. The mechanism diagram scrolls inside its
  own container rather than widening the page.

## 8. Link preview

`og.png` is **not a logo** — it's the morning receipt: the severed quote, the
exact timestamp. A stranger seeing the link in a group chat understands the whole
company before clicking. Generated by [make-card.py](make-card.py), which is also
the production renderer for every story page's card. One script, two uses, no
design tool in the loop.

## 9. Events

`page_view`, `sample_play`, `sample_finished`, `sample_missing`, `app_cta`
(with `placement`), `signup`, `signup_failed`, `signup_unwired`. Email domain
only in metadata — never the address.

The funnel: `page_view → sample_play → signup`. Week-one targets: 15 % play,
6 % signup.
