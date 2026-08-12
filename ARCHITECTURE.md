# Lullable — Website Architecture

The site has exactly two jobs, in priority order:

1. **Convert** — a lean pass-through that moves a visitor to the app (waitlist today, App Store on launch day).
2. **Attract** — a daily-post content engine that earns traffic from search (SEO) and from AI assistants (GEO).

Everything below is in service of those two jobs and nothing else.

---

## The decision: static files + a 250-line generator. No database, no CMS, no framework.

```
/                        landing page (index.html — hand-written, one file)
/sleep/                  The Sleep Library — blog index (generated)
/sleep/<slug>/           one page per post (generated)
/sitemap.xml /rss.xml /robots.txt /llms.txt   (generated)
/og.png                  share card (make-card.py)
posts/*.md               source of truth — one markdown file per post
build.py                 turns posts/ into all of the above
```

Deploy is `vercel deploy --prod` on a static folder. Cost: $0. Failure modes: approximately none — there is nothing to go down except Vercel itself.

### Why not Neon + Prisma + Next.js (yet)

A database earns its keep when data *changes at runtime* — accounts, payments, app-generated content. This site has none of that: the waitlist lives in Buttondown, events can POST to a single serverless function later, and posts change once a day at build time. A Postgres instance here would be a monthly bill and a failure mode guarding nothing.

**Migration trigger, written down now:** when the app launches and the site needs accounts, personalized cards ("your last fact" on the web), or paywalled content — *then* this becomes a Next.js app on Vercel with Neon, and the generated pages port over as static routes. The markdown files move over unchanged, which is the point of keeping them as markdown.

### Why not a free CMS for the blog

Considered honestly, because the SEO-technicals argument is real. Ruled out, for one structural reason:

**Our content is programmatic. A CMS is a UI for humans; we need an API for a habit.** The daily loop is "generate a post, publish it" — with a CMS that means driving someone else's editor or API every morning; with this setup it means writing one file and running one command. The CMS's actual value (a human-friendly editing UI for non-technical contributors) serves nobody here.

The "CMS handles SEO better" claim, itemized — this is the entire list of what a CMS would do for us, and where it lives now:

| SEO/GEO technical | Handled in |
|---|---|
| Canonical URLs, meta descriptions, OG tags | `build.py` — page template |
| `Article` + `FAQPage` JSON-LD structured data | `build.py` — from frontmatter |
| `sitemap.xml`, `rss.xml`, `robots.txt` | `build.py` — regenerated every build |
| `llms.txt` (GEO — AI crawlers get a plain-language site summary) | `build.py` |
| Clean URLs (`/sleep/slug/`), fast loads, mobile | Static files; there is nothing to be slow |

That table *is* the CMS. It's ~80 of build.py's lines and it never has an opinion, a plugin update, or a pricing change.

**The escape hatch, if the daily habit ever feels heavy:** Hashnode (free, custom domain, decent SEO defaults) can host the blog at `blog.getlullable.com` with zero maintenance. The costs would be losing the dark bedside design, the llms.txt/GEO control, and same-domain SEO authority (`/sleep/` on the root domain compounds; a subdomain partially doesn't). Take that trade only if the build step is genuinely what's stopping daily posting — which it shouldn't be, since it's one command.

---

## The GEO layer (getting cited by AI assistants)

Search traffic increasingly means being *the answer an AI gives*, not the link a person clicks. The engine is built for that:

- **`llms.txt`** — a plain-language summary of the site, the category, and every essay, regenerated on each build. AI crawlers get told exactly what Lullable is in one fetch.
- **Question-shaped posts** — frontmatter has a `question:` field; the post's first paragraph must answer it standalone (the `new` scaffold enforces the habit). That paragraph becomes the `FAQPage` structured answer — the exact unit AI assistants quote.
- **Category definition post** — "What is low-arousal learning?" exists so that when someone asks an assistant about the category, the definition cited is ours. We invented the term; we should be its source.
- **Clean semantic HTML, no JS-rendered content** — every word is in the initial response, crawlable by the dumbest bot.

## The content strategy (what the daily posts are)

Three rotating types, all downstream of what the app actually contains:

1. **Sleep questions** (SEO head terms): "why can't I stop thinking at night" — the searches our buyer makes at 1am. Warm, genuinely useful, soft CTA.
2. **Category/positioning** (GEO): definitions and comparisons we want AI assistants to repeat.
3. **Fact-worlds** (long-tail + product sampling): the episodes' subjects as quiet essays — "the weather at the bottom of the sea." These *are* the product in text form; a reader who likes one is a qualified lead.

## The daily habit

```bash
python3 build.py new the-post-slug     # scaffold posts/2026-08-12-the-post-slug.md
# write it (or have Claude write it — the voice rules live in NEWSLETTER-01.md)
python3 build.py                       # regenerate /sleep/, sitemap, rss, llms.txt
vercel deploy --prod
```

One file, two commands. If this takes more than 20 minutes a day, the posts are too long.

---

## Conversion architecture (the pass-through)

Every app CTA on the landing page is an `.app-link` with a `data-placement` tag. One constant governs them all:

- **`APP_STORE_URL = ""`** (today): every CTA reads "Join the waitlist" and scrolls to the signup module — the honest state. No fake store links.
- **Launch day**: paste the store URL into that one constant and every button on the site flips to "Get the app" / a real App Store badge. One-line launch.

Placements: header, hero badge, after-matrix, after-testimonials, after-card, plus every blog post's footer CTA. Each click tracks `app_cta` with its placement, so from day one we know which section actually converts and can delete the ones that don't — the lean-ness is enforced by data, not taste.

**Testimonials:** built in the reverse-review format, currently holding three clearly-marked draft quotes. **They must be replaced with real, permissioned Sleep Tester quotes before the site is shown to strangers** — the TODO is in the HTML. Shipping invented testimonials would poison the one asset this brand runs on, which is being believed.
