# Lullable

The low-arousal knowledge engine. Fascinating truths, told so softly that you fall asleep mid-sentence — and that's the point.

```
index.html        the landing page. one file, no build, no dependencies.
posts/*.md        The Sleep Library — one markdown file per post. git is the CMS.
catalog/*.md      six of the app's real stories, mirrored from
                  lullable_audio/Stories/<slug>/story.yaml — drives /stories/ pages
topics.json       the topic queue (~36 briefs, rotation rules embedded in the file)
build.py          validates (claim gate) + generates /sleep/, /stories/, sitemap, rss,
                  robots.txt, llms.txt, per-story share cards. stdlib only (Pillow optional).
sleep/ stories/   generated output (rebuild any time)
PRODUCTION.md     the two daily loops: essay per day, landing page per story upload
make-card.py      renders the "last fact you heard" share card / og.png. needs Pillow.
og.png            link-preview image — generated, safe to delete and remake
assets/           real app screens, story artwork, brand marks (see docs/)
fonts/            self-hosted woff2 — the site makes no third-party request
vercel.json       301s for retired story URLs + long-cache headers for assets
docs/             asset manifest + what's still missing or unverified
ARCHITECTURE.md   why static files and no CMS/DB, the GEO layer, the daily habit
MARKETING.md      go-to-market plan — audience, positioning, distribution, permission, virality
SITE.md           design system + spec behind index.html
NEWSLETTER-01.md  inaugural "Boringly Brilliant" issue, ready to send
SEQUENCE.md       onboarding letters 2–5 + the numbers that decide whether each one lives
```

Daily post habit (see PRODUCTION.md):

```bash
python3 build.py next          # scaffold, write it, then:
python3 build.py ship "Daily post: the title"
```

New story uploaded to the app:

```bash
python3 build.py story the-story-slug   # fill it in, then build + deploy
```

Regenerate a card:

```bash
python3 make-card.py og.png "the thermal vents of the Mariana Trench" "…cut mid-clause—" "Asleep by 11:41pm  ·  23 minutes of the deep ocean"
```

## Run it locally

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000

## Before launch — two one-line swaps

Both are at the top of the `<script>` in [index.html](index.html):

1. **`SUBSCRIBE_URL`** — any endpoint that accepts a POST with an `email` field.
   Fastest: create a Buttondown account and use
   `https://buttondown.com/api/emails/embed-subscribe/YOUR-USERNAME`
   (no API key, no backend, free to 100 subscribers, $9/mo after).
   Until it's set, the form tells the visitor it isn't wired up rather than faking success.

2. **`audio/sample-aristotle.mp3`** — the 3:50 sampler, mono 64kbps, cut from the
   production master with `ffmpeg -t 230 -ac 1 -b:a 64k`. Re-cut it whenever the
   episode is re-voiced, and re-derive the caption cues in index.html with it.
   Until the file exists the player says so and points at the newsletter.

`EVENTS_URL` is optional — events log to the console until it points somewhere.

**On app launch day:** paste the store link into `APP_STORE_URL` in index.html — every CTA on the site flips from "Join the waitlist" to "Get the app" in that one line.

**Testimonials:** the section is removed, not hidden. Add it back only with real,
permissioned Sleep Tester quotes. Everything else the site claims is checkable in
the app or audio workspace — see [docs/MISSING_WEBSITE_ASSETS.md](docs/MISSING_WEBSITE_ASSETS.md).

## Deploy

```bash
python3 build.py ship "what changed"
```

That's it — build, commit, push. **Vercel's GitHub integration owns the domain and
builds `main` to production on every push**, in about 30 seconds. There is no CLI to
install and no dashboard to visit.

Do *not* run `vercel deploy` here: this folder was never linked with the CLI, so it
would create a second, domain-less project and leave you wondering why getlullable.com
didn't change. Rollback, if a deploy is bad, is the Instant Rollback button on the
Vercel dashboard, or `git revert` + ship again.

Costs $0.

## Cost sheet

| Thing | Monthly |
|---|---|
| Vercel (static) | $0 |
| Buttondown (<100 subs) | $0 → $9 |
| Domain | ~$1 |
| **Total to launch** | **~$1** |

## What ships next — in order, not in parallel

1. 500 emails on the list. Measure forward rate. **If it's under 8%, the worldview is wrong — stop and fix that, not the site.**
2. Record 5 episodes. Recruit the 100 Sleep Testers.
3. Run one Midnight Salon. See if anyone writes about it.
4. Stripe Payment Link at $6/mo. No app yet — deliver episodes by private RSS feed.
5. Only then: an actual app, and only because the RSS feed can't do "the last fact you heard."
