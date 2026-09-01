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
python3 build.py ship "Daily post: the title"   # build + commit + rebase + push; Vercel builds main
# then BROWSER-VERIFY the new URL. A 200 from the deploy is not a rendered page.
```

**`ship` rebases before it pushes.** Two loops write this repo — the daily essay and
the IG scheduler — so main moving ahead between your build and your push is normal.
On 2026-08-15 that rejected a push with the post already committed. `git pull --rebase`
now runs inside `ship`; a genuine conflict stops the deploy rather than merging around it.

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
source .env && python3 ig-schedule.py --now some-slug   # publish one immediately
```

Never test against this API with throwaway content: PostPeer has no cancel or delete
route for a scheduled post, so a junk post can only be killed from the dashboard.
`--now` exists so a real card from the bank is the test.

The bank is [ig-facts.json](ig-facts.json) — sleep facts and public-domain quotes,
each with the caption it ships with. Same queue discipline as topics.json: a card is
consumed when `ig/<slug>.png` exists and its slug appears in `ig-posted.json`. Delete
both to re-open it.

Cards are 1080×1350, solid `--ink`, Newsreader, one accent rule, no photographs ever.
The renderer autofits the type so a nine-word quote and a forty-word fact land at the
same visual weight. It runs `build.py`'s claim gate over every card before writing
anything — a card is harder to retract than a page, because it is already in a feed.

**The budget is read live from `GET /v1/usage`, never guessed.** Two things make a local
tally wrong, and both were learned by running out mid-batch on 2026-08-14:

- A credit is spent when a post is **scheduled**, not when it publishes. Booking a month
  in advance bills the whole month today.
- The cycle is anchored to the **signup date — the 13th**, not the 1st. A per-calendar-month
  cap silently double-spends across the boundary: August's batch and September's first
  twelve days come out of the same 20.

The free tier is 20 per cycle. Slots are weekday evenings at 21:07 CDMX. The scheduler
HEADs every image URL before it posts anything: PostPeer fetches at publish time, so an
unpushed PNG would publish as a broken post days after you stopped watching.

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

## The loop is now unattended (2026-09-01)

`build.py next` -> draft -> gate -> `ship` -> browser-verify runs nightly at 21:00 without a
human, as the scheduled routine `lullable-daily-post`
(`~/.claude/scheduled-tasks/lullable-daily-post/SKILL.md`). It reports every run and stops
rather than improvising whenever the pre-flight, the gate or the live 200-check fails.

**Nobody reads a post before it is live now.** Three things were added the same day to carry
the weight the human read used to carry, and they are the reason the loop is safe to leave
alone:

- **`sources:` frontmatter**, hard-required on any post asserting a year, a percentage or a
  measurement. Two independent URLs minimum. Keyed on the *claim*, not on the post `type` —
  keying it on type was the first attempt and it hard-failed conceptual essays that had
  nothing to cite, which only teaches a drafter to staple on a plausible-looking link.
- **Outcome-promise phrases in `PROHIBITED`** alongside the medical ones ("fall asleep
  faster", "deeper levels of sleep", "will help you sleep"). We describe mechanism, never
  result.
- **A near-duplicate title gate**, because the queue outgrew what one person holds in their
  head and two pages answering one query split the signal instead of doubling it.

The claim gate also had a hole worth remembering: it matched against raw text, so any
multi-word phrase broken by a line wrap slid straight past it ("it will help you\nsleep
better"). Markdown wraps at ~90 chars and every prohibited phrase is 2-5 words, so it was
failing open on roughly half the copy it exists to stop. It now collapses whitespace first.

Rollback, if a post is wrong:

```bash
git revert --no-edit HEAD && python3 build.py ship "Revert: the title"
```

**Known limitation:** scheduled tasks run while the desktop app is open; if it is closed at
21:00 the run happens at next launch. If that starts costing days, move the routine to a
cloud routine, which runs server-side regardless.

## Scheduling — the reasoning that got us here

Both reference projects prove the same lesson twice: **the scheduled thing is the
thing that ships** (SIMPLE.MX: 65/100 scheduled landings published vs 120/193
unscheduled articles) — and **crons fail silently** (both projects' daily jobs were
broken on inspection day, rescued by hand).

So: the daily habit is two commands, and when you want it automated, the honest
option is a scheduled Claude routine that runs the loop *and reports failures to
you*, rather than a launchd job that no-ops quietly for a week.

That is what now runs (see above). The prediction held in the least flattering way: the
manual streak ran 2026-08-11 to 08-15 and then stopped for seventeen days with twenty-six
briefs still sitting in the queue. The engine was never the bottleneck.
