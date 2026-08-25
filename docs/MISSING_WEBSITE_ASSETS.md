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

### E. Not needed, and deliberately absent

- **App Store badge.** There is no verified store URL, so there is no badge. The
  hero CTA reads *"Coming to the App Store / Join the waitlist"* and points at
  the signup module. On launch day, paste the URL into `APP_STORE_URL` at the
  top of the `<script>` in `index.html` and every CTA on the site flips.
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
| App Store availability, price, trial terms, renewal | `PENDING` | A live App Store URL and the approved StoreKit configuration + legal copy. Until then every CTA stays "Join the waitlist". |
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

### Still open

- **Google Fonts** — resolved. The site self-hosts and makes zero third-party
  requests. See [fonts/README.md](../fonts/README.md).
- **Hero video** — still the highest-value missing asset (§A).
- **App Store URL** — the only thing standing between the current CTAs and
  "Get the app".
