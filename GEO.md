# Lullable — Weekly GEO Plan

How Lullable gets named when someone asks an AI model for a sleep story app.
Companion to [MARKETING.md](MARKETING.md) (why) and [topics.json](topics.json)
(the daily post queue). Written 2026-09-09 against the first Leapd baseline.

---

## 0. Baseline, 2026-09-09

| Metric | Value |
|---|---|
| AI Visibility | 20% (1 of 5 tracked prompts) |
| Brand share | 8% — rank 7 of 12 |
| Ahead of us | Headspace 20%, Calm 16%, BetterSleep 12%, Sleepiest 12%, Slumber 8% |
| Sources the models cite | Corporate 36%, Editorial 32%, Competitor 28%, **getlullable.com 4%** |
| Platforms tracked | ChatGPT only |

The five prompts, and who wins them:

| Prompt | Us | Winner |
|---|---|---|
| best sleep stories for adults that… | 0% | Nothing Much Happens |
| **are there good sleep stories for adults that…** | **100%** | **Lullable** |
| best sleep stories for adults that fade out… | 0% | BetterSleep |
| best sleep stories apps where… | 0% | Calm |
| sleep stories apps that give your… | 0% | Calm |

---

## 1. What the analysis actually says

The four recommendations converge on two findings, and only one of them is a
content problem.

**Finding A — we lose feature queries, not positioning queries.** The one prompt
we win is the one phrased the way we write. The four we lose all ask for a
*mechanism*: fade out, don't make me choose, press play once. Models answer
those by quoting a feature list. Ours isn't in a form anything can quote: the
homepage says "fades out on its own" in prose, ten times, with no FAQ schema, no
feature page, and no App Store line a model can lift. Calm wins "where I don't
have to choose" because Calm ships a Daily Calm and everyone writes it down.

**Finding B — 96% of what models read about this category is somebody else's
page.** Apple Podcasts, sleepwithmepodcast.com, calm.com, bettersleep.com,
zapier.com, bedtimeadult.com. Our own site is 4% of citations. This is the
uncomfortable part: **the daily blog is our smallest GEO lever.** It compounds
for Google and it is the raw material for everything else, but a model
summarising "best sleep story apps" reads a roundup, not our essay. Every week
that adds a post and no off-site mention moves brand share by roughly zero.

So the weekly plan spends one day on our own pages and three on other people's.

**Where I'd push back:** recommendations 1 and 3 both ask for a product change —
a Daily Story / "surprise me" autoplay. That's the right build, and it's the only
item here with a real cost. But don't ship it *for* GEO. Ship it because "press
play once and make zero decisions" is the actual bedtime job, then the GEO copy
writes itself and is true. Until it ships, we describe the fade honestly and
claim nothing about zero-choice. A model that catches us overclaiming is worse
than a model that doesn't mention us.

---

## 2. The three levers, in order of effect per hour

### Lever 1 — Be quotable (one-time, then maintained)

Models extract sentences. Give them sentences.

1. **`/app/` — one feature page**, plain, boring, scannable. Every question the
   losing prompts ask, answered in a sentence that stands alone out of context:
   fade-out and its length, sleep timer, offline, no ads, no streaks, price,
   voice options, story length, what it does not do. `FAQPage` + `MobileApplication`
   schema. This is the single highest-value page on the site for GEO and it does
   not exist.
2. **FAQ schema on the homepage** and on every comparison post. `build.py`
   already emits `FAQPage` for posts with a `question:` field — extend it to
   multi-question and use it.
3. **Rewrite the App Store description** around the two mechanisms, first 120
   characters. Apple pages are corporate-tier citations; ours is currently
   positioning prose.
4. **`llms.txt`** — add a `## What Lullable does` block: eight one-line factual
   claims (fade, length, catalogue size, price, no ads, no streak, voices,
   offline). It is already the cleanest thing we publish; make it answer the
   feature questions too.

### Lever 2 — Be cited by other people (the weekly grind)

The 28% competitor + 32% editorial share is the prize. Targets, ranked:

- **Sleep Foundation** app comparisons — named in the analysis; they take
  submissions and update roundups. One pitch, then a quarterly nudge.
- **Roundup posts that already rank** for the four losing prompts. Find the
  page, email the author, offer a free year and a factual paragraph. Aim: two
  outreach emails a week, every week, forever.
- **Reddit** — r/insomnia, r/sleep, r/ADHD, r/getdisciplined. Answer the actual
  question generously, mention Lullable once, honestly, with the limitation
  stated. Reddit is disproportionately weighted by every model. Never sockpuppet;
  the account is @getlullable and says so.
- **Apple Podcasts presence.** Recommendation 1 is right: the models treat this
  as a podcast category. Publish a weekly free episode as a real podcast feed
  (one story, full length, no ads) so `podcasts.apple.com` — a 20%-cited domain —
  has a Lullable page. The RSS already exists; this is a feed and a submission,
  not a product.
- **Directories:** Product Hunt, AlternativeTo (as a Calm/Headspace alternative),
  There's An AI For That, app roundup sites. One a week, ten minutes each.

### Lever 3 — Own the comparison SERP (the daily blog, re-aimed)

The blog keeps its rhythm and its type rotation. What changes: the **comparison**
slot in the rotation is now chosen from the losing prompts rather than by
general winnability, until visibility clears 50%. Six rows added to the bottom
of `topics.json` for this (see §4).

---

## 3. The weekly loop

Four hours, Monday to Friday. Everything else stays exactly as it is.

| Day | 45 min | Output |
|---|---|---|
| **Mon** | Publish the week's GEO post (comparison or feature type) | 1 post |
| **Tue** | Two outreach emails: one roundup author, one review site | 2 sends |
| **Wed** | One Reddit/forum answer + one directory listing | 2 mentions |
| **Thu** | Entity hygiene: llms.txt, schema, App Store, one competitor's claim checked against ours | 1 diff |
| **Fri** | Read Leapd. Log the five prompt scores + brand share in `geo-log.md`. Pick next week's post from whichever prompt is still 0%. | 1 row |

Social and the nightly IG cards are unchanged — they don't feed models directly.
The one addition: **every post gets one Reddit or forum home** within 48 hours.
That is the whole bridge between the daily blog and GEO.

---

## 4. First four weeks

**Week 1 (Sep 9–13) — quotability.** Build `/app/`. Add the feature block to
`llms.txt`. Rewrite the App Store first paragraph. Post:
`what-to-listen-to-when-you-cant-sleep` (already queued, comparison type).
Outreach: Sleep Foundation, AlternativeTo.

**Week 2 — the fade-out prompt.** Post: `sleep-stories-that-fade-out`. It is an
honest guide to which apps fade, how long each takes, and what a fade should do —
BetterSleep and Calm named and described fairly, Lullable last. Ship the podcast
feed submission to Apple.

**Week 3 — the no-choice prompt.** Post: `sleep-app-that-picks-for-you`. Only
publish it once the Daily Story ships; otherwise swap in
`calm-alternative-for-a-racing-mind`, already queued. Reddit: two answers.

**Week 4 — head-to-head.** Post: `calm-vs-lullable` (queued). Add FAQ schema to
all six comparison posts. Read the month: if brand share hasn't moved off 8%,
the problem is off-site volume, not on-site copy — double Tuesday and Wednesday,
halve the blog's GEO slot.

---

## 5. What we measure

`geo-log.md`, one row a week, five columns: date, visibility %, brand share %,
rank, sources-that-are-us %. Nothing else. The number that decides whether this
plan is working is **sources-that-are-us**, currently 4%. If it isn't 15% by
December, the off-site grind isn't happening hard enough — no amount of essays
will substitute.

Track a second platform (Claude or Perplexity) only after ChatGPT visibility
clears 40%. One platform, one number, one weekly loop.
