# Content Production Runbook

Two loops run this site: a **daily essay** and a **story page per app upload**.
The practices here were lifted from SAUNAS.MX and SIMPLE.MX after reviewing both
engines — what shipped, what silently broke, and why.

---

## Loop 1 — the daily essay

```bash
python3 build.py next        # picks the next topic (rotation applied), scaffolds the file, prints the brief
# write the post — or hand the printed brief to Claude with the voice contract below
python3 build.py             # validate (hard gates) + regenerate everything
python3 build.py ship "Daily post: the title"   # build + commit + push; Vercel builds main
# then BROWSER-VERIFY the new URL. A 200 from the deploy is not a rendered page.
```

**The queue** is [topics.json](topics.json) — ~36 topics, three types, rules embedded in the file.
State lives on disk: a topic is consumed when its `posts/` file exists; delete the file to re-open it.
No status fields, nothing to get out of sync (SIMPLE.MX's disk-as-queue pattern).

**Rotation**: `next` refuses to repeat the previous post's type. Fact-worlds are the
product in text form — keep them the plurality. When the queue runs dry, add topics
in the same three types; never reuse a slug.

**The voice contract** (what a generator — human or Claude — must produce):
- Frontmatter: `title`, `description` (≤155 chars), `type`, and `question:` when the post answers a search query.
- First paragraph answers the question **standalone in 30–120 words** — it becomes the FAQPage answer AI assistants quote. Explicit subjects, no "this" without a noun.
- Warm-academic register (the NEWSLETTER-01 rules): flat, unhurried, endings given away, no "here's the fascinating part," no listicles.
- 350–950 words. Never a medical claim, never a promised outcome.

**The gates** (in build.py, run before anything is written):
- **Hard fail, build aborts:** prohibited claims ("clinically proven," "cures insomnia," "guaranteed to," dosage talk — the full list is `PROHIBITED`). Negation-aware, so "Lullable is *not* a treatment" passes. A published post beats a skipped day; a published health claim is worse than nothing.
- **Hard fail:** body under 150 words (a broken generation, not a style choice).
- **Warnings, build proceeds:** description length, word count drift, answer-paragraph length, missing type.

When tuning a threshold, record the incident in the comment next to it — both source
repos' comments doubled as their decision logs, and it's the practice most worth keeping.

## Loop 2 — a landing page per story upload

When a new story ships in the app:

```bash
python3 build.py story the-story-slug    # scaffold catalog/the-story-slug.md
# fill it: metadata from the app (title, narrator, mins, genre, mood, premium),
#          blurb, a mid-clause `sample:` ending in an em-dash, the first minute,
#          and "why this one works at night"
python3 build.py ship "Story page: the-story-slug"
# browser-verify /stories/the-story-slug/
```

Each story page gets: chips, the first-minute excerpt, the ending given away
(house rules), an AudioObject + BreadcrumbList schema, **its own share card**
(rendered by make-card.py at build time — "Last night, you drifted off during …"),
and a related-content block. Story sources live in `catalog/` — they are the app's
catalog mirrored as markdown.

**Interlinking is 404-proof by construction**: related links are computed from the
files present at build time, never from the queue (SIMPLE.MX's rule — batch order
can never produce a dead link). Every essay links to 2 stories; every story links
to 3 sibling stories and 2 essays. Improving any template re-renders every page on
the next build for free.

## Loop 3 — the Instagram card

Once a month, not once a day:

```bash
.venv/bin/python make-ig.py              # render every card not yet on disk
python3 build.py ship "IG: August cards" # push — PostPeer fetches these URLs later
source .env && python3 ig-schedule.py --dry-run
source .env && python3 ig-schedule.py    # schedule the month on PostPeer
```

The bank is [ig-facts.json](ig-facts.json) — sleep facts and public-domain quotes,
each with the caption it ships with. Same queue discipline as topics.json: a card is
consumed when `ig/<slug>.png` exists and its slug appears in `ig-posted.json`. Delete
both to re-open it.

Cards are 1080×1350, solid `--ink`, Newsreader, one accent rule, no photographs ever.
The renderer autofits the type so a nine-word quote and a forty-word fact land at the
same visual weight. It runs `build.py`'s claim gate over every card before writing
anything — a card is harder to retract than a page, because it is already in a feed.

**19 posts a month is the cap**, hardcoded, because that is what PostPeer's free tier
allows. Slots are weekday evenings at 21:07 CDMX. The scheduler HEADs every image URL
before it posts anything: PostPeer fetches at publish time, so an unpushed PNG would
publish as a broken post days after you stopped watching.

Batch-scheduled deliberately — PostPeer's servers do the publishing, so there is one
thing to check each month instead of nineteen chances for a silent cron to fail.

## Failure policy (adapted from SAUNAS.MX's table)

| Failure | Behavior |
|---|---|
| Prohibited claim in any file | Build aborts, nothing written. Fix the copy. |
| Truncated/broken generation | Build aborts, names the file. |
| Pillow missing / card render error | Page ships without its custom card (falls back to site og.png), with a printed note. A missing image never blocks a publish. |
| Style drift (length, description) | Warning printed, build proceeds. |
| Deploy 200 but page broken | The reason browser-verify is a required step, not a suggestion. |

## Scheduling (not yet enabled — deliberately)

Both reference projects prove the same lesson twice: **the scheduled thing is the
thing that ships** (SIMPLE.MX: 65/100 scheduled landings published vs 120/193
unscheduled articles) — and **crons fail silently** (both projects' daily jobs were
broken on inspection day, rescued by hand).

So: the daily habit is two commands, and when you want it automated, the honest
option is a scheduled Claude routine that runs the loop *and reports failures to
you*, rather than a launchd job that no-ops quietly for a week. Ask Claude to
"schedule the daily Lullable post" and approve it — it needs your say-so, and it
should message you on failure, not just log.

Until then, the streak lives or dies on the calendar reminder. That's fine —
week one's job is proving the posts earn traffic at all.
