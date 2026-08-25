# Missing assets and unresolved claims

What the homepage would be better with, and what it is currently not allowed to
say. Nothing here blocks a production deploy — the page ships honestly without
every item — except where the row says otherwise.

---

## 1 · Assets

### A. Silent product loop for the hero — *nice to have*

The hero currently uses a still (`assets/app/screen-tonight.webp`). A short loop
would do more, and the brief's reference sites all lead with motion.

| | |
|---|---|
| What | 12–20 s screen recording, no audio: open app → Tonight → press play → set the sleep timer → screen dims |
| Format | H.264 MP4 + WebM, `muted playsinline loop`, ≤ 1.5 MB |
| Dimensions | 1179×2556 or 1290×2796 (device capture), portrait |
| Poster | First frame exported as WebP at 780w, same crop rules as the stills |
| Safe area | Keep the status bar and home indicator; do not crop the tab bar |
| Filename | `assets/app/night-loop.mp4` / `.webm` / `night-loop-poster.webp` |
| Blocks launch? | **No.** The still is real and inspectable. |

Implementation note: the hero already reserves a fixed aspect box, so a video
drops in without a layout shift. Under `prefers-reduced-motion` it must render
the poster only.

### B. Cover artwork for *Aristotle* — ✅ **DONE 2026-08-25**

`assets/art/aristotle-the-greatest-philosopher.svg` now exists, and the gallery
shows four artworks whose stories are all in the catalogue. The geometry is
derived from the story's own canonical `sigilPaths` rather than invented — see
the note in [WEBSITE_ASSET_MANIFEST.md](WEBSITE_ASSET_MANIFEST.md) § Story
artwork. It should still be reviewed by the designer who drew the other three;
if they redraw it, start from the same sigil.

### B2. Echo Contours for the remaining catalogue — *later*

Four of ~25 stories have a player artwork. Twenty-one do not, and they fall back
to a built-in mark in the app. Not a website problem today — the site only shows
the four it has — but it becomes one the moment the gallery wants to grow.

### C. Re-export recipe, if the App Store board changes

Crop boxes used against the 1290×2796 exports in
`export/appstore-iphone-6.9/`, then LANCZOS to 780w and mask corners at
`radius = 0.125 × width`:

| Source | Crop box (L, T, R, B) |
|---|---|
| `lullable-01-deeper-sleep.png` | `233, 900, 1057, 2718` |
| `lullable-04-wonderful.png` | `233, 900, 1057, 2718` |
| `lullable-02-the-sleep-library.png` | `142, 441, 1148, 2659` |
| `lullable-03-now-playing.png` | `142, 441, 1148, 2659` |

### D. Story pages: 6 of ~25 published — *by choice*

`catalog/*.md` holds six of the app's production-verified stories, picked to
cover all four genres with **one story per narrator**. The other ~19 are ready to
add whenever they are wanted: everything a page needs already exists in
`lullable_audio/Stories/<slug>/story.yaml` and `narration.md`, and the frontmatter
contract is title / narrator / mins / genre / mood / premium / date / base / glow /
accent / sigil / blurb / sample. Adding one is `python3 build.py story <slug>`,
fill it in, ship.

Two of the catalogue's stories carry the narrator string `Lullable` rather than a
persona (*The Deep Ocean Trenches*, *The Observatory on Ben Nevis*, *The Bakery
Before Dawn*, *The Great Library of Alexandria*). They were skipped for the first
six so every page could name a real reader. Worth reconciling in the app before
those get pages.

### E. Apple's official App Store badge — *optional, and only once live*

The hero CTA used to be a recreation of Apple's badge: their logo glyph plus a
two-line *"Download on the / App Store"* lockup. Apple's Marketing Resources
allow that lockup **only as the complete artwork they supply, unmodified**, and
separately forbid using the Apple logo in your own marketing art. It has been
replaced with a plain Lullable button — the mark, *"On the App Store / Get the
app"* — which is allowed with no asset at all.

If the real badge is wanted:

| | |
|---|---|
| What | Apple's official "Download on the App Store" badge, black variant, taken from Apple's Marketing Resources and **not redrawn** |
| Format | SVG |
| Filename | `assets/brand/appstore-badge.svg` |
| Blocks launch? | **No.** `build.py golive` notices the file and tells you to swap it into the hero button; without it the plain button ships. |

### F. Not needed, and deliberately absent
- **Press logos, award marks, ratings graphics.** None are earned yet.
- **Testimonial portraits.** No permissioned quotes exist (see §2).

---

## 2 · Claims: `PENDING`, changed, or omitted

### Changed in this pass

| Was | Now | Why |
|---|---|---|
| Morning card: *"Asleep by 11:41pm"* | *"Last listened at 11:41 pm · 23 min of ancient worlds"* | `MorningView.swift` renders a **last-listened position**. The app does not detect sleep onset and must not imply it. Fixed on the page **and** in `make-card.py`'s default, so every generated share card inherits the correction. |
| Morning card statement invented for the site | *"You left off while listening to …"* | Verbatim from the app's own `statement` string. |
| *"Seven free nights when it arrives. No card, and the trial ends by itself."* | **Removed** | Unverified. No trial length, price or renewal behaviour is stated anywhere the website can check. Restore only against StoreKit product configuration + legal sign-off. |
| Fabricated CSS recreation of the app's home screen | Four real screens | The old hero phone was hand-drawn in CSS with catalogue titles that are not in the app. |

### Still `PENDING` — omitted from the public page

| Item | Status | What would clear it |
|---|---|---|
| App Store **availability** | `PENDING`, and gated in code | The record exists — App Store Connect app **GetLullable, Apple ID `6800138113`** (`PRODUCTION_PHASE_0_DECISIONS.md`, confirmed 2026-08-12) — so the URL will be `https://apps.apple.com/app/id6800138113`. **Apple's public lookup returns nothing for it in us/mx/gb as of 2026-08-25**, i.e. the listing does not resolve. Nothing is hardcoded; see § Launch day below. |
| Price, trial terms, renewal | `PENDING` | Approved StoreKit configuration + legal sign-off. The live copy currently says only "Free to download" and "Aristotle is free to listen to", both of which are true of the shipped catalogue. Any number — price, trial length, renewal — needs adding by hand and checking. |
| Ratings, review counts, download numbers, awards, editor's features | `PENDING` | Nothing to cite. The proof strip uses **product truths** instead (sleep timer, background playback, resume, morning receipt) — all four verified on a physical iPhone 12 per the app's own `VERIFICATION_MATRIX.md`. |
| Sleep-tester testimonials | `PENDING` | Three illustrative drafts remain in git history; the section stayed removed. Replace only with real, permissioned quotes. |
| "Never a notification after 9 pm" | **Stated as a promise, not a measurement** | It is a stated operating promise on the signup module, alongside the other three permission terms. It is not presented as a technical guarantee of the app. |
| Number of stories in the app | `PENDING`, omitted | `production-catalog.json` currently holds **one** story (Aristotle); `catalog.json` holds six, four of which are 1-minute stubs. The page therefore never states a catalogue size — it names the four real genres and shows real titles only. |

### Fixed 2026-08-25 — the invented story pages

`catalog/*.md` used to drive six `/stories/` pages — *Rain on the Glasshouse*,
*Cartography of Small Islands*, *The Lamplighter's Round*, *The Slow Train
North*, *Snowfall over the Orchard*, *The Keeper of the Tide Clock*. None of
those titles was in the app's catalogue, and each page's CTA said the story
"lives in the Lullable app."

All six are gone, replaced by six real ones. Because the old URLs were indexed,
`vercel.json` 301s each retired slug to its nearest real equivalent, and the one
essay that linked to a retired story (*The Standard Railway Gauge* → *The Slow
Train North*) now links to *The Midnight Sleeper Train Across the Alps*.

**The site no longer asserts any product fact that the app cannot support.**

## 3 · Launch day

The flip is one command, and it **refuses to run early**:

```bash
python3 build.py appstore     # read-only: is the listing live yet?
python3 build.py golive       # flips everything — only if Apple says it is
python3 build.py              # regenerate /sleep/, /stories/, legal pages
python3 build.py ship "Launch: get the app"
```

`appstore` asks Apple's public lookup API for `6800138113` in the us/mx/gb
storefronts and prints what it finds. `golive` asks the same question and
**exits non-zero if the answer is no** — an App Store Connect record exists long
before the page resolves, and a CTA pointing at a dead listing is worse than an
honest waitlist. `golive --force` exists for the propagation window and prints a
loud warning.

What `golive` changes, all in one go:

1. `APP_STORE_URL` in `index.html`.
2. Every `.app-link` rewritten **statically** — href and label — so the served
   HTML says "Get the app" before a line of script runs. (The runtime rewrite
   still exists; it is now a belt to the braces.)
3. The eight pre-launch strings marked `data-live-text` in the HTML take their
   successors, which are authored **now**, next to what they replace, so launch
   copy is reviewed today rather than written in a hurry on the day. Without
   this, the buttons would say "Get the app" while the page still said
   *"Be there the night it opens."*
4. The join form's button loses `.solid` — post-launch it is the newsletter, and
   the filled treatment belongs to the store CTAs.
5. Safari's Smart App Banner meta (`apple-itunes-app`) is added.
6. `manifesto/index.html`, the other hand-written page, gets the same treatment.

`/sleep/`, `/stories/`, `/privacy/` and `/terms/` are generated and read the same
constant through `app_cta()`, so they flip on the next `build.py`. **There is one
source of truth and no second place to forget.**

The whole flip has been dry-run end to end: 8 strings swapped, 3 CTAs
repointed, 22 generated files updated, zero leftover "waitlist" wording in the
served markup, zero console errors — then reverted. It is proven, not hoped.

### Still open

- **Google Fonts** — resolved. The site self-hosts and makes zero third-party
  requests. See [fonts/README.md](../fonts/README.md).
- **Hero video** — the highest-value missing asset (§A).
- **The App Store listing itself** — the only thing left. Everything the site
  needs to do about it is written and tested.
