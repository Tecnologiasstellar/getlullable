#!/usr/bin/env python3
"""
The Sleep Library + Story pages — static generator. Zero runtime dependencies
(Pillow optional, for per-story share cards). Git is the CMS; disk is the queue.

    python3 build.py                 # validate + build everything
    python3 build.py next            # pick the next topic from topics.json (rotation
                                     #   rules applied) and scaffold its post
    python3 build.py new <slug>      # scaffold an off-queue post
    python3 build.py story <slug>    # scaffold a story page (new app upload)
    python3 build.py ship "msg"      # build + commit + push = deployed to production
    python3 build.py ping            # tell IndexNow what the last commit changed
    python3 build.py ping --all      # resubmit every page (after a redesign)

Pipeline principles, imported from SAUNAS.MX and SIMPLE.MX and recorded here
so they survive refactors:
  - Disk is the queue state. A topic is consumed when its posts/ file exists;
    delete the file to re-open the topic. No status fields anywhere.
  - The generator (human or Claude) writes prose into typed slots (frontmatter
    + constrained markdown). THIS script assembles pages, schema, and feeds —
    structure is never left to generation.
  - Hard gates for expensive failures (medical/sleep claims), warnings for
    cheap ones (length drift). A published post beats a skipped day; a
    published health claim is worse than nothing. Hard failures abort the
    whole build, loudly, before anything is written.
  - Interlinking only ever targets files that exist on disk at build time,
    so batch order can never produce a dead link.
  - Rendering is pure: improving a template here re-renders every page on the
    next build for free.
"""
import html, json, re, sys, unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

import spanish   # every Spanish word this script prints; the site is also published under /es/

ROOT = Path(__file__).parent
SITE = "https://getlullable.com"          # <- the one config value
BRAND = "Lullable"

APPLE_ID = "6800138113"   # App Store Connect record "GetLullable", confirmed 2026-08-12
# The canonical listing, as Apple's own lookup returns it (trackViewUrl, minus
# the ?uo=4 affiliate parameter). The short /app/id<id> form redirects here, so
# every CTA, badge and installUrl points at the destination rather than the hop.
STORE_URL = f"https://apps.apple.com/us/app/lullable-adult-sleep-stories/id{APPLE_ID}"

# ---------------------------------------------------------------- claim gate
# The expensive failure. Sleep is health-adjacent: we never promise outcomes,
# never sound clinical, never touch dosage. Negation within the same sentence
# is allowed (40-char lookback, stopped at sentence break) so "this is not a
# treatment" and myth-debunking pass. Modeled on SIMPLE.MX's invented-price
# gate and SAUNAS.MX's prohibitedClaimsIn().
PROHIBITED = [
    "cures insomnia", "cure insomnia", "cure your insomnia",
    "treats insomnia", "treat insomnia", "treatment for insomnia",
    "clinically proven", "scientifically proven", "medically proven",
    "guaranteed to", "doctor recommended", "doctors recommend",
    "diagnose", "prescription strength", "melatonin dose", "dosage",
    # Outcome promises. Added 2026-09-01 when the daily post became unattended:
    # nobody reads a draft before it is live now, and an unsupervised drafter
    # drifts toward exactly the register the category markets in (Slumber's own
    # App Store subtitle is "Fall Asleep in 5 Minutes"). We describe mechanism,
    # never a result. Each phrase below was checked against every existing file
    # first — bare "in minutes", "guarantee" and "sleep aid" are NOT here because
    # they have legitimate uses already on the site ("the loop point within
    # minutes", "counting guarantees you stay awake", "Boredom as a sleep aid").
    "fall asleep faster", "fall asleep quicker", "asleep in minutes",
    "deeper levels of sleep", "improves sleep quality", "improve your sleep",
    "proven to", "will help you sleep", "helps you fall asleep",
    "help you sleep better", "get you to sleep",
]
# Spanish topics entered the queue 2026-09-17 and the loop is unattended, so the
# list below stopped being allowed to be English-only. Phrases are written WITHOUT
# accents because prohibited_claims_in() strips them before matching — otherwise
# "clínicamente" and "clinicamente" would need two entries each, and the drafter
# only has to drop an accent to walk through the gate.
PROHIBITED += [
    "cura el insomnio", "curar el insomnio", "cura para el insomnio", "cura tu insomnio",
    "trata el insomnio", "tratar el insomnio", "tratamiento para el insomnio",
    "tratamiento del insomnio",
    "clinicamente probado", "cientificamente probado", "medicamente probado",
    "clinicamente comprobado", "cientificamente comprobado",
    "recomendado por medicos", "los medicos recomiendan", "recomendado por doctores",
    "diagnosticar", "dosis de melatonina", "dosificacion",
    # The outcome promises. Same reasoning as the English block above: describe
    # mechanism, never a result. "Te ayudara a dormir mejor" is the single most
    # natural sentence in Spanish sleep marketing, which is exactly why it is here.
    "te ayuda a dormir", "te ayudara a dormir", "ayuda a dormir mejor",
    "ayudarte a dormir", "te ayudara a conciliar",
    "dormiras mas rapido", "te duermes mas rapido", "duermete mas rapido",
    "dormirte mas rapido", "conciliar el sueno mas rapido",
    "mejora la calidad del sueno", "mejora tu sueno", "mejorar tu sueno",
    "mejora el sueno", "garantizado que", "te garantiza", "probado para",
]

NEGATORS = ("not ", "n't ", "never ", "no ", "isn't ", "aren't ", "won't ", "without ",
            "nunca ", "sin ", "ni ", "jamas ", "tampoco ")

def prohibited_claims_in(text):
    # Collapse whitespace before matching. Found 2026-09-01: markdown prose wraps
    # at ~90 chars, so "it will help you\nsleep better" slid straight past a gate
    # searching raw text. Every phrase here is 2-5 words, so a line break lands
    # inside one roughly as often as not — the gate was failing open on exactly
    # the copy it exists to stop. Positions stay consistent for the negation
    # lookback below because it reads the same collapsed string.
    low = re.sub(r"\s+", " ", text.lower())
    # Strip diacritics so one unaccented entry covers both spellings. English
    # phrases are unaffected; Spanish ones would otherwise be bypassed by the
    # commonest typo in the language.
    low = "".join(c for c in unicodedata.normalize("NFKD", low)
                  if not unicodedata.combining(c))
    hits = []
    for phrase in PROHIBITED:
        for m in re.finditer(re.escape(phrase), low):
            window = low[max(0, m.start() - 40):m.start()]
            cut = max(window.rfind("."), window.rfind("!"), window.rfind("?"))
            window = window[cut + 1:]
            if not any(n in window for n in NEGATORS):
                hits.append(phrase)
    return sorted(set(hits))

# ---------------------------------------------------------------- markdown

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    return s

def md(body):
    out = []
    for block in re.split(r"\n\s*\n", body.strip()):
        lines = block.strip().split("\n")
        if lines[0].startswith("### "):
            out.append(f"<h3>{inline(lines[0][4:])}</h3>")
            if lines[1:]: out.append(f"<p>{inline(' '.join(lines[1:]))}</p>")
        elif lines[0].startswith("## "):
            out.append(f"<h2>{inline(lines[0][3:])}</h2>")
            if lines[1:]: out.append(f"<p>{inline(' '.join(lines[1:]))}</p>")
        elif all(l.startswith("- ") for l in lines):
            out.append("<ul>" + "".join(f"<li>{inline(l[2:])}</li>" for l in lines) + "</ul>")
        elif all(re.match(r"\d+\. ", l) for l in lines):
            out.append("<ol>" + "".join(f"<li>{inline(l.split('. ', 1)[1])}</li>" for l in lines) + "</ol>")
        elif all(l.startswith("> ") for l in lines):
            out.append(f"<blockquote>{inline(' '.join(l[2:] for l in lines))}</blockquote>")
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    return "\n".join(out)

def first_paragraph(body):
    for block in re.split(r"\n\s*\n", body.strip()):
        if not block.startswith(("#", ">", "-")):
            return re.sub(r"[*\[\]]|\([^)]*\)", "", block.replace("\n", " ")).strip()
    return ""

def wordcount(body):
    return len(re.findall(r"\w+", body))

# ---------------------------------------------------------------- parsing

def parse(path):
    raw = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        sys.exit(f"HARD FAIL {path.name}: missing frontmatter")
    meta = dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.M))
    d, slug = path.stem[:10], path.stem[11:]
    return {"date": d, "slug": slug, "body": m.group(2), "path": path.name, **meta}

def parse_story(path):
    raw = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        sys.exit(f"HARD FAIL {path.name}: missing frontmatter")
    meta = dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.M))
    return {"slug": path.stem, "body": m.group(2), "path": path.name, **meta}

# ---------------------------------------------------------------- validation
# Hard fails abort the build. Warnings print and proceed.
# Thresholds carry their reasons — keep the comments when tuning.

def validate_post(p, warnings):
    errs = []
    for field in ("title", "description"):
        if not p.get(field):
            errs.append(f"missing {field}")
    if len(p.get("description", "")) > 160:   # Google truncates ~155-160 by pixel width
        warnings.append(f"{p['path']}: description {len(p['description'])} chars (aim ≤155)")
    hits = prohibited_claims_in(p["body"] + " " + p.get("title", "") + " " + p.get("description", ""))
    if hits:
        errs.append(f"prohibited claim(s): {', '.join(hits)}")
    wc = wordcount(p["body"])
    if wc < 150:                              # broken/truncated generation, not style
        errs.append(f"body only {wc} words — looks like a failed generation")
    elif not 350 <= wc <= 950:
        warnings.append(f"{p['path']}: {wc} words (target 350–950)")
    if p.get("question"):
        fp = first_paragraph(p["body"])
        fw = len(fp.split())
        # the first paragraph IS the FAQ answer AI assistants quote; it must stand alone
        if not 30 <= fw <= 120:
            warnings.append(f"{p['path']}: answer paragraph {fw} words (target 30–120, self-contained)")
    if p.get("lang") and p["lang"] not in LOCALES:
        errs.append(f"lang must be one of {'|'.join(LOCALES)}, got {p['lang']!r}")
    if not p.get("type"):
        warnings.append(f"{p['path']}: no type: (question|definition|fact-world) — rotation can't see it")
    # Sources, required wherever the post makes a CHECKABLE claim. Added
    # 2026-09-01 with unattended publishing: the claim gate above catches
    # medical language, but it has nothing to say about whether the Ben Nevis
    # observatory really ran 1883-1904. Two independent URLs make a fabrication
    # visible instead of invisible.
    #
    # Keyed on the claim, not on the `type`. Keying it on type was the first
    # attempt and it was wrong: what-is-low-arousal-learning and
    # what-are-sleep-stories are conceptual essays containing no date, figure
    # or attribution at all, and a rule that hard-fails them only teaches the
    # drafter to staple on a plausible-looking link. A citation nobody needed
    # is worse than no citation, because it looks like diligence.
    srcs = sources_of(p)
    bad = [u for u in srcs if not u.startswith(("http://", "https://"))]
    if bad:
        errs.append(f"sources must be URLs: {', '.join(bad)}")
    bad_prices = unlisted_prices(p["body"])
    if bad_prices:
        errs.append(f"price(s) not in prices.json: {', '.join(bad_prices)} — add them with a "
                    f"vendor-page source and today's date, or remove them")
    claims = checkable_claims(p["body"])
    if claims and len(srcs) < 2:
        errs.append(f"{len(srcs)} source(s) but makes checkable claims "
                    f"({', '.join(claims[:4])}) — needs 2+ sources: URLs")
    if not claims and not srcs and p.get("type") == "fact-world":
        warnings.append(f"{p['path']}: a fact-world with no checkable claim and no sources "
                        f"— is it actually about something?")
    return errs


# ---------------------------------------------------------------- price gate
# Comparison posts are the one place this site makes falsifiable claims about
# other companies, and a wrong price destroys the credibility the whole page
# runs on. So every price printed in an essay must be listed in prices.json,
# read from the vendor's own page, with the date it was last seen. Modelled on
# SIMPLE.MX's invented-price gate. Scoped to posts/ — legal/terms.md carries a
# US$100 liability cap that is not a product price.
PRICE_RE = re.compile(r"(?<![A-Za-z])\$\s?\d[\d,]*(?:\.\d{2})?")
STALE_DAYS = 90

def known_prices():
    try:
        data = json.loads((ROOT / "prices.json").read_text())
    except (OSError, ValueError):
        return set(), []
    ok, stale = set(), []
    for name, rec in data.get("prices", {}).items():
        for field in ("monthly", "yearly", "once"):
            if rec.get(field):
                ok.add(rec[field].replace(" ", ""))
        try:
            age = (date.today() - datetime.strptime(rec["checked"], "%Y-%m-%d").date()).days
            if age > STALE_DAYS:
                stale.append(f"{name}: price checked {age} days ago ({rec['checked']}) — re-read {rec.get('source','?')}")
        except (KeyError, ValueError):
            stale.append(f"{name}: missing or unparseable `checked` date")
    return ok, stale


def unlisted_prices(body):
    ok, _ = known_prices()
    return sorted({m.group(0).replace(" ", "") for m in PRICE_RE.finditer(body)} - ok)


# A year, a percentage, or a measurement. Deliberately narrow: it should fire on
# "Between 1883 and 1904" and "1,086 bar", and stay quiet on the spelled-out
# numbers the house voice prefers ("cycles of roughly ninety minutes"), which
# are the ones a reader cannot check anyway.
CLAIM_PATTERNS = [
    r"\b(?:1[5-9]|20)\d{2}\b",
    r"\b\d[\d,.]*\s?(?:%|per cent|percent)",
    r"\b\d[\d,.]*\s?(?:metres|meters|feet|miles|kilometres|kilometers|km|"
    r"degrees|bar|atmospheres|tonnes|tons)\b",
]

def checkable_claims(body):
    hits = []
    for pat in CLAIM_PATTERNS:
        hits += [m.group(0).strip() for m in re.finditer(pat, body, re.I)]
    return sorted(set(hits))


def sources_of(p):
    """The `sources:` frontmatter, as a list of URLs. Comma-separated."""
    return [u.strip() for u in p.get("sources", "").split(",") if u.strip()]


# Near-duplicate titles. The queue outgrew what one person holds in their head
# (the 4am variant sits right next to the live 3am page, and "mind won't shut
# off" next to why-cant-i-stop-thinking-at-night), and two pages answering one
# query split the signal instead of doubling it. Jaccard over content words at
# 0.7: "Why do I wake up at 3am with my mind racing?" vs "Why am I wide awake at
# 4am every night?" scores well under it, so genuine variants still ship.
STOPWORDS = {"a", "an", "and", "are", "at", "be", "but", "can", "do", "does", "for",
             "how", "i", "in", "is", "it", "me", "my", "of", "on", "or", "the",
             "to", "we", "what", "when", "why", "you", "your", "t", "s"}

def title_tokens(t):
    return {w for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in STOPWORDS}

def duplicate_titles(posts):
    errs = []
    for i, a in enumerate(posts):
        for b in posts[i + 1:]:
            ta, tb = title_tokens(a["title"]), title_tokens(b["title"])
            if not ta or not tb:
                continue
            overlap = len(ta & tb) / len(ta | tb)
            if overlap >= 0.7:
                errs.append(f"{a['path']} and {b['path']}: titles {overlap:.0%} identical "
                            f"— cannibalisation. Retitle or delete one.")
    return errs

def validate_story(s, warnings):
    errs = []
    for field in ("title", "narrator", "voice", "mins", "genre", "mood", "blurb", "sample", "date"):
        if not s.get(field):
            errs.append(f"missing {field}")
    if not str(s.get("mins", "")).isdigit():
        errs.append(f"mins must be a number, got {s.get('mins')!r}")
    # voice drives /stories/male-voice/ and /stories/female-voice/ — the only
    # narrator facet with both verified search demand and matching inventory.
    # Declared, never guessed from the narrator's name.
    if s.get("voice") and s["voice"] not in ("male", "female"):
        errs.append(f"voice must be male|female, got {s['voice']!r}")
    hits = prohibited_claims_in(s["body"] + " " + s.get("blurb", ""))
    if hits:
        errs.append(f"prohibited claim(s): {', '.join(hits)}")
    if s.get("sample") and not s["sample"].rstrip().endswith("—"):
        warnings.append(f"{s['path']}: sample should end mid-clause with an em-dash — the truncation is the joke")
    return errs

# ---------------------------------------------------------------- templates

CSS = """
/* ── Fonts, self-hosted ──────────────────────────────────────────
   No Google Fonts request: the browser never tells a third party who is
   reading a sleep-stories site at 1am, and /privacy/ can say so plainly.
   These are the same latin-subset woff2 files Google serves, kept locally.
   Both families are SIL Open Font License 1.1 — see fonts/README.md.
   Variable weight axes, so one file covers every weight in use.
   ─────────────────────────────────────────────────────────────── */
@font-face{font-family:Inter;font-style:normal;font-weight:300 600;font-display:swap;
  src:url(/fonts/inter-latin.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:Newsreader;font-style:italic;font-weight:300 500;font-display:swap;
  src:url(/fonts/newsreader-italic-latin.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:Newsreader;font-style:normal;font-weight:300 500;font-display:swap;
  src:url(/fonts/newsreader-latin.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
/* "Nocturne" — the iOS app's palette, shared with index.html so the site and the
   app are one product. The old amber is retired: the app has no amber. The
   variable names are kept so the rules below did not all have to be rewritten;
   --amber now names the one accent, which is a line, a border and a glow, never
   a flood. */
:root{--ink:#161826;--ink-2:#232532;--ink-3:#1C1E2B;--haze:rgba(233,233,237,.14);--text:#E9E9ED;--dim:#B2B6CA;
--dimmer:#8E92A8;--cream:#ECE4D3;--amber:#9184D9;--amber-soft:rgba(145,132,217,.4);--iris:#B5ABFC;--iris-dim:#9184D9;
--serif:Newsreader,Iowan Old Style,Palatino,Georgia,serif;
--sans:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
*{box-sizing:border-box;margin:0}
body{background:var(--ink);color:var(--text);font:400 17px/1.65 var(--sans);-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0 0 auto;height:50vh;pointer-events:none;
background:radial-gradient(110% 70% at 50% 0%,rgba(145,132,217,.07),transparent 62%)}
/* wide frame, centered reading measure — the measure protects the paragraphs,
   the frame gives everything else room to breathe */
.wrap{position:relative;max-width:56rem;margin:0 auto;padding:0 1.5rem}
.measure{max-width:36rem;margin-inline:auto}
header{padding:1.75rem 0}
.bar{display:flex;align-items:center;justify-content:space-between;gap:1rem}
/* the official lockup: four echo-contour arcs beside a serif wordmark (assets/brand/logo.svg) */
.mark{display:inline-flex;align-items:center;gap:.6rem;min-height:44px;font:400 21px/1 var(--serif);
letter-spacing:.01em;text-transform:lowercase;text-decoration:none;color:#E9D6B6}
.mark img{width:38px;height:19px}
.bar nav{display:flex;align-items:center;gap:1.4rem;font-size:.875rem;color:var(--dim)}
.bar nav a{text-decoration:none}
.bar nav a:hover{color:var(--text)}
.navbtn{border:1.5px solid var(--cream);color:var(--cream);border-radius:11px;padding:.55rem 1rem;
transition:background .18s ease}
.navbtn:hover{background:rgba(236,228,211,.10);color:var(--cream)}
@media(max-width:560px){.bar nav a:nth-child(-n+2){display:none}}
h1{font-family:var(--serif);font-weight:400;font-size:clamp(2rem,4.5vw,2.7rem);line-height:1.18;letter-spacing:-.015em;margin:0 0 1rem}
h2{font-family:var(--serif);font-weight:400;font-size:1.4rem;margin:2.5rem 0 1rem}
h3{font-family:var(--serif);font-weight:400;font-size:1.15rem;margin:2rem 0 .75rem}
.post-head{text-align:center;padding:2.5rem 0 2rem;max-width:42rem;margin-inline:auto}
.eyebrow{font:500 .75rem/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--iris-dim);margin-bottom:1.25rem}
.post-meta{font-size:.82rem;color:var(--dimmer)}
.post-meta b{color:var(--dim);font-weight:400}
/* a pitch page's sub-headline: readable, not a document's date line */
.post-meta.tagline{font-family:var(--serif);font-size:1.08rem;line-height:1.55;color:var(--dim);max-width:32rem;margin-inline:auto}
.meta{font:500 .75rem/1.5 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--iris-dim);margin-bottom:2.5rem}
article p{font-family:var(--serif);font-size:1.08rem;line-height:1.75;color:var(--dim);margin-bottom:1.3rem}
article strong{color:var(--text);font-weight:400;font-style:italic}
article a{color:var(--text)}
article ul,article ol{margin:0 0 1.3rem 1.2rem;color:var(--dim);font-family:var(--serif);font-size:1.08rem;line-height:1.75}
article ol li{padding-left:.25rem;margin-bottom:.4rem}
article ol li::marker{color:var(--iris-dim);font-family:var(--sans);font-size:.9rem}
article blockquote{border-left:2px solid var(--amber-soft);padding-left:1.25rem;margin:2rem 0;
font-family:var(--serif);font-style:italic;font-size:1.1rem;line-height:1.7;color:var(--dim)}
/* the short answer — the block AI assistants and skimmers both take */
.answer{background:linear-gradient(160deg,#232532,#161826);border:1px solid var(--haze);border-radius:16px;
padding:1.6rem 1.75rem;margin:0 0 2.5rem;box-shadow:0 12px 30px rgba(0,0,0,.5)}
.answer .lbl{font:500 .75rem/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--amber);margin-bottom:.8rem}
.answer p{margin:0;color:var(--text);font-size:1.12rem}
.chips{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:2rem;justify-content:center}
.chip{font:500 .75rem/1 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--iris-dim);
background:rgba(145,132,217,.12);border:1px solid rgba(145,132,217,.22);border-radius:20px;padding:.45rem .8rem}
.chip.amber{color:var(--cream);background:rgba(236,228,211,.10);border-color:rgba(236,228,211,.28)}
.cta{background:linear-gradient(160deg,#232532,#161826);border:1px solid var(--haze);border-radius:16px;
padding:1.75rem;margin:3.5rem 0;text-align:center;box-shadow:0 12px 30px rgba(0,0,0,.5)}
.cta p{font-family:var(--serif);color:var(--dim);margin-bottom:1.25rem}
/* The one filled button, spent on the one action a story page wants. */
.cta a{display:inline-flex;align-items:center;min-height:52px;background:var(--cream);color:var(--ink);
border:1.5px solid var(--cream);border-radius:14px;padding:.85rem 1.5rem;text-decoration:none;
font-size:1rem;font-weight:500;transition:background .18s ease,transform .1s ease-out}
.cta a:hover{background:#F5F0E6}
/* Feedback lives on the press, and it is instant — not on release. */
.cta a:active{transform:scale(.97)}
/* The page-top CTA: just the button under the headline, no card. The card is
   for the end of the page, where a box earns its keep by stopping the scroll. */
.cta-top{background:none;border:0;box-shadow:none;padding:0;margin:0 0 2.75rem}
.cta-note{font:400 .85rem/1.5 var(--sans);color:var(--dimmer);margin:.9rem 0 0}
.cta .cta-note{margin-bottom:0}
.cta .cta-note a{display:inline;min-height:0;background:none;border:0;border-radius:0;padding:0;
font:inherit;color:var(--iris);text-decoration:underline;text-underline-offset:2px}
.cta .cta-note a:hover{background:none;color:var(--cream)}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
/* related content as cards; stories carry the app's gradient covers */
.sources{border-top:1px solid var(--haze);margin-top:2.5rem;padding-top:1.25rem}
.sources .lbl{font:500 .7rem/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--dim);margin-bottom:.6rem}
.sources ul{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:.5rem .9rem}
.sources li{font:400 .82rem/1.4 var(--sans)}
.sources a{color:var(--dim);text-decoration:underline;text-underline-offset:3px}
.sources a:hover{color:var(--text)}
.related{border-top:1px solid var(--haze);margin-top:3.5rem;padding-top:2.5rem}
.related h2{margin-top:0;font-size:1.25rem;text-align:center;margin-bottom:1.75rem}
.rel-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1rem}
.rel{display:block;text-decoration:none;background:var(--ink-2);border:1px solid var(--haze);border-radius:14px;
padding:1.1rem;transition:border-color .3s}
.rel:hover{border-color:rgba(145,132,217,.35)}
.cover{display:block;border-radius:10px;margin-bottom:.9rem;overflow:hidden}
.hero-cover{max-width:240px;margin:0 auto 1.6rem}
.hero-cover .cover{border-radius:18px;border:1px solid var(--haze)}
.g0{background:linear-gradient(150deg,#423A6A,#161826)}.g1{background:linear-gradient(150deg,#2B2741,#161826)}
.g2{background:linear-gradient(150deg,#5D5294,#1C1E2B)}.g3{background:linear-gradient(150deg,#262A60,#161826)}
.rel .kind{font:500 .75rem/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--dimmer);display:block;margin-bottom:.4rem}
.rel .t{font-family:var(--serif);font-size:1rem;line-height:1.35;color:var(--text)}
@media(max-width:700px){.rel-grid{grid-template-columns:1fr 1fr}}
@media(max-width:480px){.rel-grid{grid-template-columns:1fr}}
footer{padding:3rem 0 3.5rem;font-size:.8rem;color:var(--dimmer);text-align:center}
footer a{color:var(--dimmer)}
/* index: card grid */
.idx-head{text-align:center;padding:2.5rem 0 .5rem}
.idx-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:2.5rem;list-style:none}
.idx-card{background:var(--ink-2);border:1px solid var(--haze);border-radius:16px;padding:1.5rem;
display:flex;flex-direction:column;transition:border-color .3s}
.idx-card:hover{border-color:rgba(145,132,217,.35)}
.idx-card .row{display:flex;justify-content:space-between;align-items:center;margin-bottom:.9rem}
.idx-card time,.idx-card .sub{font-size:.75rem;color:var(--dimmer)}
.idx-card a{font-family:var(--serif);font-size:1.3rem;line-height:1.3;color:var(--text);text-decoration:none}
.idx-card a:hover{color:var(--iris)}
.idx-card p{color:var(--dim);font-size:.92rem;margin-top:.6rem;line-height:1.6}
@media(max-width:700px){.idx-grid{grid-template-columns:1fr}}
::selection{background:rgba(145,132,217,.3)}
"""

def plain(answer):
    """An APP_FACTS/FAQ_FACTS answer as plain text. The page may carry a link in
    an answer; the FAQPage schema and llms.txt must not — a crawler quoting
    `<a href=...>` back at a reader is the whole GEO bet lost to a stray tag."""
    return re.sub(r"<[^>]+>", "", answer)


def post_cta(line=None, note=None, lang="en"):
    """The App Store is the one button. `note` is for anything that must stay
    beside it without competing with it — the Sunday letter, which is a
    different offer to a different reader and should not look like the app."""
    href, label = app_cta()
    line = line or tr("Lullable reads material like this aloud — warmly, slowly, and quieter "
                      "every minute —\nuntil you drift off somewhere around the fourth clause.", lang)
    note = f'\n<p class="cta-note">{note}</p>' if note else ""
    return f'<div class="cta">\n<p>{line}</p>\n<a href="{href}">{tr(label, lang)}</a>{note}\n</div>'

def story_cta(s, lang="en"):
    href, label = app_cta()
    line = tr("{title} is {mins} minutes long, read by {narrator}, and ends quieter than it "
              "begins. It lives in the Lullable app.", lang).format(
        title=html.escape(s["title"]), mins=s["mins"], narrator=html.escape(s["narrator"]))
    return f'<div class="cta">\n<p>{line}</p>\n<a href="{href}">{tr(label, lang)}</a>\n</div>'

# `lang` is the language of the whole page, chrome included: English at the root,
# Mexican Spanish under /es/ with the same slugs. A post declares `lang: es` in its
# frontmatter and is published under /es/sleep/. The two languages were one page
# template until the Spanish site (2026-09-24); they still are, and the Spanish
# words live in spanish.py so the English here stays readable.
LOCALES = {"en": "en_US", "es": "es_MX"}
# The tag each language is published under: <html lang> and hreflang. English
# keeps the plain "en" it has always declared; the Spanish is written for Mexico.
HREFLANG = {"en": "en", "es": "es-MX"}
LANGUAGE_NAMES = {"en": "English", "es": "Español"}

def site_path(lang, path):
    """"/app/" -> "/es/app/" in Spanish. Same slugs in both languages, on purpose."""
    return f"/es{path}" if lang == "es" else path

def tr(s, lang):
    """A template string in the page's language. The Spanish lives in spanish.UI,
    keyed by the English it replaces, so the English stays readable where it is
    used — and an English line edited without its twin shows up as a warning at
    build time instead of an English sentence on a Spanish page, unnoticed."""
    if lang == "en":
        return s
    if s not in spanish.UI:
        print(f"  warn: no Spanish for {s[:70]!r} — the Spanish page shows it in English")
    return spanish.UI.get(s, s)

def page(title, desc, canonical, body, extra_head="", og_image=None, lang="en", alt=None):
    """`alt` is the same page in the other language, when there is one: it adds
    the hreflang tags to the head and a one-word switcher to the footer. A page
    with no twin gets neither — hreflang only ever points at a real translation,
    and the switcher never drops a reader on some other page's homepage."""
    nav_href, nav_label = app_cta()
    # One og:image only. Crawlers (WhatsApp, Facebook) take the FIRST tag, so a
    # per-page card appended after the default was silently never shown.
    og_image = og_image or f"{SITE}/og.png"
    pre = site_path(lang, "")
    hreflang = switch = ""
    if alt:
        en, es = (canonical, alt) if lang == "en" else (alt, canonical)
        # es-MX alone speaks to Spanish speakers in Mexico, and Google may send the
        # rest (Spain, Colombia, the US) to x-default, the English page. The plain
        # "es" makes this the page for all of them; same four tags in the sitemap.
        hreflang = (f'<link rel="alternate" hreflang="en" href="{en}">\n'
                    f'<link rel="alternate" hreflang="es-MX" href="{es}">\n'
                    f'<link rel="alternate" hreflang="es" href="{es}">\n'
                    f'<link rel="alternate" hreflang="x-default" href="{en}">\n')
        other = "es" if lang == "en" else "en"
        switch = (f' · <a href="{alt[len(SITE):]}" hreflang="{HREFLANG[other]}" '
                  f'lang="{HREFLANG[other]}">{LANGUAGE_NAMES[other]}</a>')
    # The feed is the English Sleep Library; a Spanish page does not advertise it.
    rss = ("" if lang == "es" else f'<link rel="alternate" type="application/rss+xml" '
           f'title="{BRAND} — The Sleep Library" href="{SITE}/rss.xml">\n')
    footer = (spanish.FOOTER.format(year=date.today().year) if lang == "es" else
              f"""{BRAND} — the low-arousal knowledge engine. Not a medical device.
<br>Sleep Library essays are drafted with Claude against a fixed voice contract, checked against the sources listed on each page, and published unedited. Spot an error? <a href="mailto:info@getlullable.com">Tell us</a> and we will correct it.
· <a href="/">Home</a> · <a href="/app/">The app</a> · <a href="/faq/">FAQ</a> · <a href="/manifesto/">Manifesto</a> · <a href="/sleep/">The Sleep Library</a> · <a href="/stories/">Stories</a> · <a href="/#signup">Newsletter</a>
<br><a href="https://www.instagram.com/getlullable/" rel="me noopener" target="_blank">Instagram</a> · <a href="https://www.tiktok.com/@getlullable" rel="me noopener" target="_blank">TikTok</a> · <a href="https://www.youtube.com/@lullableapp" rel="me noopener" target="_blank">YouTube</a> · <a href="https://www.facebook.com/profile.php?id=61594011460380" rel="me noopener" target="_blank">Facebook</a>
<br>© {date.today().year} Tecnologías Stellar, S.A. de C.V. · developed by <a href="https://stellartech.xyz" rel="noopener" target="_blank">stellartech.xyz</a> · <a href="/creators/">Creators</a> · <a href="/support/">Support</a> · <a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a> · <a href="#" data-consent>Cookie settings</a>""")
    return f"""<!doctype html>
<html lang="{HREFLANG[lang]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="{canonical}">
{hreflang}<meta property="og:title" content="{html.escape(title)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="{LOCALES.get(lang, 'en_US')}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
{rss}<link rel="icon" href="/assets/brand/web/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/brand/web/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/brand/web/apple-touch-icon.png">
<link rel="preload" as="font" type="font/woff2" href="/fonts/inter-latin.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="/fonts/newsreader-latin.woff2" crossorigin>
<script>window.va=window.va||function(){{(window.vaq=window.vaq||[]).push(arguments)}};</script>
<script defer src="/_vercel/insights/script.js"></script>
{extra_head}<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="bar">
<a class="mark" href="{pre}/"><img src="/assets/brand/mark.svg" width="38" height="19" alt="" decoding="async">{BRAND.lower()}</a>
<nav><a href="{pre}/stories/">{tr("Stories", lang)}</a><a href="{pre}/sleep/">{tr("The Sleep Library", lang)}</a><a href="{pre}/chronotype/">{tr("Chronotype quiz", lang)}</a><a class="navbtn" href="{nav_href}">{tr(nav_label, lang)}</a></nav>
</header>
{body}
<footer>{footer}{switch}</footer>
</div>
<script src="/consent.js" defer></script>
</body>
</html>"""

def sources_html(p, lang="en"):
    """Where the facts came from, printed on the page.

    Not decoration: the daily post is drafted unattended, so the reader (and we)
    need to be able to check a date against the thing it came from. Bare-domain
    labels keep it quiet enough to sit under a warm-academic essay."""
    srcs = sources_of(p)
    if not srcs:
        return ""
    items = "".join(
        f'<li><a href="{html.escape(u, quote=True)}" rel="noopener nofollow" '
        f'target="_blank">{html.escape(re.sub(r"^https?://(www\.)?", "", u).split("/")[0])}</a></li>'
        for u in srcs)
    return f'<div class="sources"><div class="lbl">{tr("Sources", lang)}</div><ul>{items}</ul></div>\n'


def jsonld(schemas):
    # <-escape so no copy can break out of the script tag (SIMPLE.MX convention)
    return "".join('<script type="application/ld+json">'
                   + json.dumps(s).replace("<", "\\u003c")
                   + "</script>\n" for s in schemas)

def pretty(d, lang="en"):
    t = datetime.strptime(d, "%Y-%m-%d")
    if lang == "es":   # month names by hand: the system locale is not ours to rely on
        return f"{t.day} de {spanish.MONTHS[t.month - 1]} de {t.year}"
    return t.strftime("%B %-d, %Y")

def related_html(items, lang="en"):
    # items: list of (url, title, kind, cover) — cover is ready-made markup for
    # stories, "" for essays. Only ever built from files on disk.
    if not items:
        return ""
    cards = "".join(
        f'<a class="rel" href="{u}">' + (cov or "")
        + f'<span class="kind">{k}</span><span class="t">{html.escape(t)}</span></a>'
        for u, t, k, cov in items)
    return f'<div class="related">\n<h2>{tr("Keep drifting", lang)}</h2>\n<div class="rel-grid">{cards}</div>\n</div>'

def cover_class(slug):
    """Essays have no artwork of their own; they borrow one of four grounds."""
    return f"g{sum(ord(c) for c in slug) % 4}"

def story_cover(s, height="64px"):
    """The story's real cover, rebuilt from the app's StoryVisualIdentity:
    a radial ground from `glow` (UnitPoint .5/.16, end radius .62) to `base` at
    .68, with the story's own sigilPaths stroked in `accent` at 2.6 in the
    100-unit sigil space. Colours and paths come from the catalog frontmatter,
    which mirrors lullable_audio/Stories/<slug>/story.yaml. A story missing
    either half falls back to a plain ground rather than to an invented mark —
    the app makes the same choice for the same reason."""
    base, glow, accent = s.get("base"), s.get("glow"), s.get("accent")
    if not (base and glow):
        return f'<span class="cover {cover_class(s["slug"])}" style="height:{height}"></span>'
    ground = (f"radial-gradient(62% 62% at 50% 16%,#{glow} 0%,#{base} 68%)")
    marks = ""
    if s.get("sigil") and accent:
        # five stroked elements is the design rule; the pipeline enforces it too
        els = [e.strip() for e in s["sigil"].split("|") if e.strip()][:5]
        paths = []
        for e in els:
            d, _, op = e.rpartition("@")
            d, op = (d or e).strip(), (op.strip() or "1")
            paths.append(f'<path d="{html.escape(d, quote=True)}" opacity="{op}"/>')
        marks = ('<svg viewBox="0 0 100 100" fill="none" aria-hidden="true" '
                 'preserveAspectRatio="xMidYMid meet" style="position:absolute;inset:0;'
                 'width:100%;height:100%">'
                 f'<g stroke="#{accent}" stroke-width="2.6" stroke-linecap="round" '
                 'stroke-linejoin="round">' + "".join(paths) + '</g></svg>')
    return (f'<span class="cover" style="height:{height};background:{ground};position:relative">'
            f'{marks}</span>')

def read_minutes(body):
    return max(1, round(wordcount(body) / 210))

# ---------------------------------------------------------------- story cards

def share_card(path, when, quote, footer, headline=None):
    """A share image via make-card.py. Optional: a missing card must never
    block a publish. If this python lacks Pillow, retry with the macOS system
    python (/usr/bin/python3), which ships with it here — homebrew's python3
    took over PATH on 2026-08-11 and silently dropped the cards."""
    args = (str(path), when, quote, footer, headline or "")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("makecard", ROOT / "make-card.py")
        mc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mc)
        mc.card(*args[:4], headline=headline)
        return True
    except Exception:
        import subprocess
        r = subprocess.run(["/usr/bin/python3", str(ROOT / "make-card.py"), *args],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return True
        print(f"  note: no share card for {path} ({r.stderr.strip()[:80] or 'no Pillow found'})")
        return False

def story_card(s, outdir, lang="en"):
    return share_card(outdir / "og.png", s["title"], f"“{s['sample'].strip()}”",
                      tr("{mins} minutes · read by {narrator}", lang).format(
                          mins=s["mins"], narrator=s["narrator"]),
                      headline=tr("Last night, you drifted off during {title}.", lang).format(
                          title=s["title"]))

# ---------------------------------------------------------------- chronotype quiz
# /chronotype/ — the reduced Morningness–Eveningness Questionnaire (Adan &
# Almirall, 1991): five questions, scored 4–25, mapped onto five animals. The
# result page IS the share page: the quiz redirects to /chronotype/<animal>/,
# which carries its own OG card, so a WhatsApp preview reads "I'm an Owl" and
# the friend lands one tap from taking it themselves. That is the whole loop.
CHRONO_Q = [
    ("If you were entirely free to plan your day, when would you get up?",
     [("Between 5:00 and 6:30", 5), ("6:30 to 7:45", 4), ("7:45 to 9:45", 3),
      ("9:45 to 11:00", 2), ("11:00 or later", 1)]),
    ("In the first half hour after waking, how do you feel?",
     [("Very tired", 1), ("Fairly tired", 2), ("Fairly refreshed", 3), ("Very refreshed", 4)]),
    ("In the evening, when do you start to feel tired and in need of sleep?",
     [("8:00 to 9:00 pm", 5), ("9:00 to 10:15 pm", 4), ("10:15 pm to 12:45 am", 3),
      ("12:45 to 2:00 am", 2), ("2:00 am or later", 1)]),
    ("At what time of day do you feel at your best?",
     [("5 to 8 am", 5), ("8 to 10 am", 4), ("10 am to 5 pm", 3),
      ("5 to 10 pm", 2), ("10 pm to 5 am", 1)]),
    ("People talk about morning types and evening types. Which are you?",
     [("Definitely a morning type", 6), ("More morning than evening", 4),
      ("More evening than morning", 2), ("Definitely an evening type", 0)]),
]
# slug, name, article, lowest score, type line, description, the share line.
# Lullable's own five: quiet, true animals from the story world, morning to night.
CHRONO = [
    ("blackbird", "Blackbird", "a", 22, "Definitely a morning type",
     "The first voice in the dawn chorus, singing before there is light to sing by. "
     "Your best hour is one most people sleep through, and by nine in the evening the "
     "day has quietly closed behind you. The trouble is rarely falling asleep. It is "
     "the world expecting you to be awake at ten.",
     "up before the sun and asleep before the news."),
    ("tortoise", "Tortoise", "a", 18, "Moderately a morning type",
     "An early riser who keeps to the daylight and is in no hurry inside it. You wake "
     "without much of a fight, do your clearest thinking before lunch, and fade in step "
     "with the evening. Late nights are possible, but they are paid for the next morning.",
     "my day runs on daylight, and I take it slowly."),
    ("sheep", "Sheep", "a", 12, "Neither, and in good company",
     "Neither lark nor owl, and the most common of the five, which seems fitting. You "
     "wake with the light, work best through the middle of the day, and are ready for "
     "bed a while after dark. Your rhythm follows the sun, give or take an hour, which "
     "is why a routine suits you so well.",
     "the most common chronotype, and the only one that gets counted."),
    ("moth", "Moth", "a", 8, "Moderately an evening type",
     "The evening is where you come alive, usually near a lamp. Mornings are a "
     "negotiation, the afternoon is fine, and somewhere after dinner the ideas start "
     "arriving. Midnight feels like a reasonable bedtime, even when the alarm disagrees.",
     "my best ideas arrive after dinner, usually near a lamp."),
    ("octopus", "Octopus", "an", 4, "Definitely an evening type",
     "You do not properly get going until the sun has gone down. Midnight is early; "
     "one or two is more honest. Mornings, when they cannot be avoided, are endured. "
     "The mind that keeps you up is the same one that does its best work at eleven at "
     "night, and with three hearts' worth of curiosity it needs somewhere quiet to go "
     "when it is done.",
     "midnight is early and my brain clocks off long after I do."),
]
CHRONO_CSS = """<style>
.q{border:0;padding:0;margin:0 0 2.2rem}
.q legend{font-family:var(--serif);font-size:1.15rem;line-height:1.4;color:var(--text);margin-bottom:.9rem}
.q label{display:flex;align-items:center;gap:.8rem;padding:.8rem 1rem;margin-bottom:.5rem;border:1px solid var(--haze);
border-radius:12px;background:var(--ink-2);color:var(--dim);cursor:pointer;transition:border-color .18s}
.q label:hover{border-color:rgba(145,132,217,.45)}
.q label:has(:checked){border-color:var(--amber);background:rgba(145,132,217,.10);color:var(--text)}
.q input{accent-color:var(--amber);width:18px;height:18px;margin:0;flex:none}
.go{display:flex;align-items:center;justify-content:center;width:100%;min-height:54px;background:var(--cream);color:var(--ink);
border:1.5px solid var(--cream);border-radius:14px;padding:.85rem 1.5rem;font:500 1rem var(--sans);cursor:pointer}
.go:hover{background:#F5F0E6}
.share{display:flex;flex-wrap:wrap;gap:.6rem;margin:1.75rem 0 1rem}
.share a,.share button{display:inline-flex;align-items:center;min-height:48px;border:1.5px solid var(--cream);color:var(--cream);
background:none;border-radius:14px;padding:.7rem 1.2rem;font:500 .95rem var(--sans);text-decoration:none;cursor:pointer}
.share a:hover,.share button:hover{background:rgba(236,228,211,.10)}
.animals{list-style:none;padding:0;margin:1.5rem 0 0;display:grid;gap:.75rem}
.animals a{display:block;text-decoration:none;background:var(--ink-2);border:1px solid var(--haze);border-radius:14px;
padding:1rem 1.2rem;color:var(--dim);font-size:.95rem;line-height:1.5;transition:border-color .3s}
.animals a b{display:block;font:400 1.15rem var(--serif);color:var(--text)}
.animals a:hover{border-color:rgba(145,132,217,.35)}
</style>
"""

def chrono_set(lang):
    """(questions, animals) in one language. The Spanish twins sit in spanish.py
    with the same slugs, scores and thresholds, so a result URL is the same page
    in both languages."""
    return (spanish.CHRONO_Q, spanish.CHRONO) if lang == "es" else (CHRONO_Q, CHRONO)

def chrono_share_text(c, lang="en"):
    slug, name, art, _, _, _, line = c
    return tr("I'm {art} {name}: {line} Find your sleep chronotype in two minutes:", lang).format(
        art=art, name=name, line=line)

def chrono_animals(skip=None, lang="en"):
    base = site_path(lang, "/chronotype/")
    items = "".join(
        f'<li><a href="{base}{c[0]}/"><b>{c[1]}</b>{c[4]}. {html.escape(c[5].split(". ")[0])}.</a></li>'
        for c in chrono_set(lang)[1] if c[0] != skip)
    return f'<ul class="animals">{items}</ul>'

def chrono_cta(lang="en"):
    href, label = app_cta()
    line = tr("Whatever hour you finally lie down, the moment is the same: a mind still running. "
              "Lullable reads you true, quietly fascinating things in a voice that gets softer "
              "every minute, so the thinking has somewhere to go.", lang)
    return f'<div class="cta">\n<p>{line}</p>\n<a href="{href}">{tr(label, lang)}</a>\n</div>'

def build_chronotype(lang="en"):
    """Writes /chronotype/ (the quiz) and /chronotype/<animal>/ (five result
    pages, each with its own share card) in one language. Returns their URLs
    for the sitemap."""
    from urllib.parse import quote
    other = "es" if lang == "en" else "en"
    base = site_path(lang, "/chronotype/")
    questions, animals = chrono_set(lang)
    out = ROOT / base.strip("/"); out.mkdir(parents=True, exist_ok=True)
    qs = ""
    for i, (q, opts) in enumerate(questions):
        rows = "".join(f'<label><input type="radio" name="q{i}" value="{v}" required>{html.escape(t)}</label>'
                       for t, v in opts)
        qs += f'<fieldset class="q"><legend>{i + 1}. {html.escape(q)}</legend>{rows}</fieldset>\n'
    buckets = "".join(f's>={c[3]}?"{c[0]}":' for c in animals[:-1]) + f'"{animals[-1][0]}"'
    t = lambda s: tr(s, lang)
    body = f"""<div class="post-head"><p class="eyebrow">{t("Five questions, two minutes")}</p>
<h1>{t("What's your sleep chronotype?")}</h1>
<p class="post-meta">{t("Lullable has a rule against quizzes. This is the one exception: there are no wrong answers and nothing to remember.")}</p></div>
<article class="measure">
<p>{t("Most of when you want to sleep was decided for you. A roughly 24-hour clock in your body cues when you feel sharp, when you feel hungry and when you finally feel tired, and your <strong>chronotype</strong> is where that clock sits against everyone else's. Early types peak before lunch. Late types come alive after dark. Most people sit somewhere in the middle, and the setting drifts with age: children run early, teenagers run late.")}</p>
<p>{t("The five questions below are adapted from the reduced Morningness–Eveningness Questionnaire, the short form of the instrument sleep researchers have used since 1976. Answer for the life you would choose, not the one your alarm imposes.")}</p>
<form id="quiz">
{qs}<button class="go" type="submit">{t("Reveal my chronotype")}</button>
</form>
<h2>{t("The five animals")}</h2>
{chrono_animals(lang=lang)}
<p class="post-meta" style="margin-top:2rem">{t("Adapted from Adan &amp; Almirall (1991), the reduced form of Horne &amp; Östberg's questionnaire. A tendency, not a diagnosis. Chronotypes drift with age and nothing here is medical advice.")}</p>
</article>
<script>
document.getElementById("quiz").addEventListener("submit",function(e){{
  e.preventDefault();
  var s=0;new FormData(e.target).forEach(function(v){{s+=+v}});
  var t={buckets};
  try{{sessionStorage.setItem("lull_chrono",t)}}catch(_){{}}
  location.href="{base}"+t+"/";
}});
</script>"""
    (out / "index.html").write_text(page(
        t("What's your sleep chronotype? A two-minute quiz — Lullable"),
        t("Five questions from the sleep researchers' own questionnaire, and one of five animals at the end. Blackbird, tortoise, sheep, moth or octopus?"),
        f"{SITE}{base}", body, CHRONO_CSS, lang=lang, alt=f"{SITE}{site_path(other, '/chronotype/')}"))
    urls = [f"{SITE}{base}"]

    for c in animals:
        slug, name, art, lo, kind, desc, line = c
        url = f"{SITE}{base}{slug}/"
        d = out / slug; d.mkdir(exist_ok=True)
        has_card = share_card(d / "og.png", name, line[0].upper() + line[1:],
                              t("Find your sleep chronotype in two minutes · five animals, no wrong answers"),
                              headline=t("I'm {art} {name}.").format(art=art, name=name))
        og = f"{url}og.png" if has_card else f"{SITE}/og.png"
        text = chrono_share_text(c, lang)
        # Spanish needs the article the English folds into "The": el mirlo, la tortuga.
        heading = t("The {name}").format(name=name, the=spanish.ARTICLES.get(art, ""))
        body = f"""<div class="post-head"><p class="eyebrow" id="eb">{t("A sleep chronotype")}</p>
<h1 id="h">{heading}</h1>
<p class="post-meta">{t("{kind} · one of five").format(kind=kind)}</p></div>
<article class="measure">
<p>{html.escape(desc)}</p>
<div class="share">
<button id="sh" hidden>{t("Share my result")}</button>
<a href="https://wa.me/?text={quote(text + ' ' + url)}" target="_blank" rel="noopener">WhatsApp</a>
<a href="https://x.com/intent/post?text={quote(text)}&amp;url={quote(url)}" target="_blank" rel="noopener">X</a>
<button id="cp">{t("Copy link")}</button>
</div>
<p class="post-meta">{t('Not you? <a href="{quiz}">Take the two-minute quiz</a>.').format(quiz=base)}</p>
{chrono_cta(lang)}
<h2>{t("The other four")}</h2>
{chrono_animals(skip=slug, lang=lang)}
</article>
<script>
(function(){{
var slug="{slug}",url="{url}",text={json.dumps(text)},mine=false;
try{{mine=sessionStorage.getItem("lull_chrono")===slug}}catch(_){{}}
if(mine){{document.getElementById("eb").textContent="{t("Your chronotype")}";
  document.getElementById("h").textContent="{t("You’re {art} {name}.").format(art=art, name=name)}";}}
var sh=document.getElementById("sh"),cp=document.getElementById("cp");
if(navigator.share){{sh.hidden=false;sh.onclick=function(){{navigator.share({{text:text,url:url}}).catch(function(){{}})}}}}
cp.onclick=function(){{navigator.clipboard.writeText(url).then(function(){{cp.textContent="{t("Copied")}"}})}};
}})();
</script>"""
        (d / "index.html").write_text(page(
            t("I'm {art} {name}. What's your sleep chronotype?").format(art=art, name=name),
            t("{kind}: {line} Five questions, two minutes, no wrong answers.").format(
                kind=kind, line=line[0].upper() + line[1:]),
            url, body, CHRONO_CSS, og_image=og, lang=lang,
            alt=f"{SITE}{site_path(other, f'/chronotype/{slug}/')}"))
        urls.append(url)
    print(f"built chronotype quiz + {len(animals)} result pages -> {base.strip('/')}/")
    return urls


# ---------------------------------------------------------------- /app/
# The feature page. Its whole job is to be quotable by an answer engine.
#
# The Leapd baseline (GEO.md, 2026-09-09) says we score 0% on every tracked
# prompt that asks for a mechanism — "sleep stories that fade out", "an app
# where I don't have to choose" — and 100% on the one phrased the way we
# write. Models answer mechanism questions by lifting a sentence. The
# homepage says "it fades out on its own" ten times in prose and there was
# nowhere on this site a sentence could be lifted from.
#
# So: one question per heading, one self-contained answer under it, and the
# same list emitted three ways — as the page, as FAQPage schema, and as the
# "What Lullable does" block in llms.txt. One source, no second copy to drift.
#
# Every line here is checked against the shipping app as described on the
# homepage's product-truth strip and walkthrough. Nothing aspirational goes
# in. One deliberate omission remains: no offline claim (unverified). The
# price is now published on the listing, so it is quoted here — with the
# storefront and the fact that Apple sets it, because a price a model repeats
# is a price we are held to. Re-read the listing when it changes.

CATALOGUE_SIZE = 26        # stories published to production, lullable-content, 2026-08-22

APP_FACTS = [
    ("What is Lullable?",
     f"Lullable is an iPhone app of long-form sleep stories for adults: {CATALOGUE_SIZE} true, "
     "gently fascinating pieces \u2014 a Roman bathhouse at closing time, the life of a redwood, "
     "the rings of Saturn \u2014 read slowly and flatly by a named narrator, and engineered "
     "so you fall asleep partway through. It is "
     f'<a href="{STORE_URL}">on the App Store</a>, free to download.'),

    ("Do the stories fade out on their own?",
     "Yes. A sleep timer set to 15, 30, 45 or 60 minutes ends in a ten-second ramp down to "
     "silence rather than a hard stop. Every recording also ends that way on its own: the "
     "last thirty seconds of every story fade out. There is nothing to switch off."),

    ("Do I have to choose a story?",
     "No. The first screen is Tonight, and it holds one story already chosen for you, with "
     "one Play button. No feed, no library to browse with a phone six inches from your face. "
     "The full library is there if you want it, but it is the second screen, not the first."),

    ("How long are the stories?",
     "Between 20 and 41 minutes. Most run about 40 \u2014 long enough that you are not "
     "expected to reach the end, which is the point."),

    ("What are the stories about?",
     "Four categories: Ancient Worlds, Cosmic Journeys, Gentle Nature and Cozy Tales. All of "
     "it is true material rather than fiction, told in order, with the ending given away in "
     "the first line so there is never a reason to stay awake for it."),

    ("Are there ads?",
     "No. Lullable has no advertising in it, and no version of this business has one \u2014 "
     "a mid-roll at 3am wakes the person it is sold to."),

    ("Does it keep playing when the screen locks?",
     "Yes. Background and lock-screen playback, with the transport on the lock screen. "
     "Put the phone face down and leave it."),

    ("Where does it start again the next night?",
     "A minute before you lost the thread \u2014 not at the point the audio stopped, which "
     "is always later than the point you stopped hearing it."),

    ("Is there a streak, a score or a sleep graph?",
     "None of the three. The morning screen shows the last line you heard and the time you "
     "stopped listening. That is all it knows and all it claims. There is no number to "
     "improve on and nothing to keep up."),

    ("Who reads the stories?",
     "Named narrators, in male and female voices \u2014 David from Oxford, Amy from "
     "Greenwich, Arthur from Ludlow, Brian from St Ives, Niamh from Kinsale, Patrick from "
     "Block Island. Every one reads flat and warm, removing emphasis rather than adding it, "
     "and gets quieter across the episode."),

    ("What does it cost?",
     "Free to download, with one story \u2014 Aristotle, the Greatest Philosopher, 33 "
     "minutes \u2014 free to listen to in full. The rest of the catalogue needs Lullable "
     "Premium, which is $2.99 a month or $19.99 a year on the US App Store today. Apple sets "
     "the price in each country and it can change, so the listing is the figure that counts."),

    ("Is there an Android version?",
     "Not yet. iPhone only."),

    ("Is Lullable a medical device or a treatment for insomnia?",
     "No, and it does not claim to be. It is audio designed for people whose minds will not "
     "stand down at night. If you have clinical insomnia, see a doctor."),
]


APP_CTA_LINE = ("Lullable is on the App Store. Free to download, and one 40-minute story is "
                "free to listen to end to end before you pay for anything.")
APP_CTA_NOTE = ('Prefer to read? The Sunday letter is three quiet paragraphs of history or '
                'physics, once a week — <a href="/#signup">join it here</a>.')


def spanish_facts(facts):
    """spanish.py's fact lists say {catalogue} and {store}; the figures themselves
    stay here, in one place, so a catalogue change reaches both languages."""
    return [(q, a.format(catalogue=CATALOGUE_SIZE, store=STORE_URL)) for q, a in facts]


def build_app_page(lang="en"):
    """Writes /app/ \u2014 every feature question, answered in one liftable sentence."""
    t = lambda s: tr(s, lang)
    other = "es" if lang == "en" else "en"
    path = site_path(lang, "/app/")
    out = ROOT / path.strip("/"); out.mkdir(parents=True, exist_ok=True)
    url = f"{SITE}{path}"
    facts = spanish_facts(spanish.APP_FACTS) if lang == "es" else APP_FACTS

    qa = "\n".join(f"<h3>{html.escape(q)}</h3>\n<p>{a}</p>" for q, a in facts)
    body = f'''<article>
<div class="post-head"><p class="eyebrow">{t("The app")}</p>
<h1>{t("What Lullable actually does")}</h1>
<p class="post-meta">{t("Every question about the app, answered in one sentence. Last updated")} <time datetime="{date.today()}">{pretty(str(date.today()), lang)}</time>.</p></div>
<div class="measure">
<div class="answer"><div class="lbl">{t("The short answer")}</div>
<p>{t("Lullable is an iPhone app of {catalogue} long-form sleep stories for adults. One story is chosen for you on the first screen, so there is nothing to decide at bedtime; a timer set to 15, 30, 45 or 60 minutes fades to silence rather than stopping; and every recording fades out on its own in its last thirty seconds. No ads, no streak, no sleep score.").format(catalogue=CATALOGUE_SIZE)}</p></div>
{qa}
</div>
{post_cta(t(APP_CTA_LINE), t(APP_CTA_NOTE), lang)}
</article>'''

    schemas = [
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer", "text": plain(a)}}
                        for q, a in facts]},
        {"@context": "https://schema.org", **app_schema_node(
            description=t("Long-form sleep stories for adults, read slowly and fading to silence."))},
    ]
    (out / "index.html").write_text(page(
        t("What Lullable actually does \u2014 the app, feature by feature"),
        t("Does it fade out? Do I have to choose a story? How long are they? Every question "
          "about the Lullable sleep-story app, answered in one sentence."),
        url, body, jsonld(schemas), lang=lang, alt=f"{SITE}{site_path(other, '/app/')}"))
    print(f"built {path} ({len(facts)} answered questions + FAQPage schema)")
    return url


FAQ_CSS = """<style>
/* Ten questions, all on one screen. <details> rather than a script: the answers
   sit in the initial HTML either way (a crawler and the FAQPage schema never see
   the closed state), and a native disclosure is keyboard- and screen-reader-
   correct for free. Two columns from 900px, where a 56rem frame has the room.
   NOTE: page() injects this BEFORE the shared sheet, so anything that collides
   with a CSS class in it needs the extra class to win the tie (.post-head), and
   the phone block has to be the last thing in this file. */
.post-head.faq-head{padding:2rem 0 1.4rem}
.faq-lead{max-width:40rem;margin-inline:auto;text-align:center;color:var(--dim);font-size:1.02rem;line-height:1.6}
.faq-list{display:grid;gap:.5rem;margin:1.6rem 0 0}
/* two independent columns, not a two-wide grid: in a grid, opening one answer
   grew the whole row and left a hole beside it */
.faq-col{display:grid;gap:.5rem;align-content:start}
@media(min-width:900px){.faq-list{grid-template-columns:1fr 1fr;gap:.9rem;align-items:start}}
.faq-list details{border:1px solid var(--haze);border-radius:12px;background:var(--ink-2);
transition:border-color .18s}
.faq-list details:hover{border-color:rgba(145,132,217,.35)}
.faq-list details[open]{border-color:var(--amber-soft);background:rgba(145,132,217,.07)}
.faq-list summary{display:flex;gap:.8rem;align-items:baseline;list-style:none;cursor:pointer;
padding:.85rem 1.1rem;min-height:48px;font:400 1.02rem/1.4 var(--serif);color:var(--text)}
.faq-list summary::-webkit-details-marker{display:none}
.faq-list summary::after{content:"+";margin-left:auto;flex:none;color:var(--dimmer);
font:300 1.25rem/1 var(--sans);align-self:center}
.faq-list details[open] summary::after{content:"−";color:var(--iris)}
.faq-list summary:hover{color:var(--iris)}
.faq-list summary:focus-visible{outline:2px solid var(--iris);outline-offset:-2px;border-radius:12px}
.faq-list .a{margin:0;padding:0 1.1rem 1.05rem;color:var(--dim);font-size:.94rem;line-height:1.7}
.faq-foot{text-align:center;margin-top:1.6rem}
@media(max-width:700px){.post-head.faq-head{padding:1rem 0 .8rem}
.faq-head h1{font-size:1.95rem}
.faq-lead{font-size:.93rem;line-height:1.55}
.faq-list{margin-top:1rem;gap:.35rem}
.faq-list summary{padding:.62rem .9rem;min-height:44px;font-size:.95rem}
.faq-foot{margin-top:1.2rem}}
</style>
"""

# ---------------------------------------------------------------- /faq/
# The second quotable page. /app/ answers *feature* questions ("does it fade
# out?") for someone already looking at the app. This one answers the
# questions a stranger types at 1am — how it works, whether it is worth
# paying for, how it differs from Calm, from a podcast, from rain sounds.
#
# Different job, so a different page: overlapping FAQPage blocks on one
# domain compete with each other. Nothing here repeats a question from
# APP_FACTS; when a reader wants the feature detail, we link to /app/.
#
# Rules that apply to every answer below:
#   - It must stand alone out of context. A model lifts one <p>, not a page.
#   - Mechanism, never outcome. The claim gate in this file bans "fall asleep
#     faster" and its family for good reason; the honest version of our
#     pitch is how the thing is built, not what it will do to you.
#   - Any competitor price comes from prices.json with its source and date.

FAQ_FACTS = [
    ("How does Lullable work?",
     "You press play once. A named narrator reads you a true story — the life of a "
     "redwood, a Roman bathhouse at closing time, the rings of Saturn — slowly, flatly, "
     "and a little quieter every minute. Somewhere in the middle you stop following it. The "
     "story carries on without you and fades to silence on its own. In the morning the app "
     "shows the last line you heard and the time you stopped, and the next night it starts "
     "again a minute before that. There is nothing to set up, nothing to score and nothing "
     "to finish."),

    ("Why does a story quiet a racing mind when lying still doesn’t?",
     "Because a mind that will not stop can be occupied more easily than it can be emptied. "
     "Lying in the dark gives your attention nothing to hold, so it returns to the email, the "
     "mortgage, the thing you said in 2011. A true story told in order, at a flat pitch, with "
     "no jeopardy and the ending given away in the first line, gives attention somewhere dull "
     "to rest. That is the entire design of the app. It is a mechanism, not a promise — "
     "sleep is not a thing software can hand you."),

    ("How much does Lullable cost?",
     "The app is free to download, and one full story — Aristotle, the Greatest "
     "Philosopher, 33 minutes — is free to listen to end to end, so you can test the "
     "voice on your own pillow before paying anything. The rest of the catalogue needs "
     "Lullable Premium: $2.99 a month or $19.99 a year on the US App Store today. Apple sets "
     "the price in each country and it can change, so the listing is the figure that counts. "
     "For what the category charges today: Calm is $14.99 a "
     "month and Headspace is $12.99 a month on the US App Store, both read at the source "
     "on September 7, 2026."),

    ("Is a sleep-story app worth paying for?",
     "Test it before you decide, which is why the free story is not a trailer: same length, "
     "same narrator, same fade as the paid ones. A week of it tells you more than any review. "
     "What a subscription adds is the rest of the catalogue — 26 stories, a new one most "
     "weeks — and an app with no advertising in it, which matters more at 1am than "
     "anywhere else, because a mid-roll wakes precisely the person it was sold to. Set the "
     "monthly figure against the forty minutes a night you already spend on the phone "
     "instead, and decide from there."),

    ("How is Lullable different from Calm or Headspace?",
     "Calm and Headspace are broad wellness apps — meditation, breathwork, music, "
     "courses, celebrity readings, with a sleep section among them. Lullable does one thing: "
     "long-form true stories for adults, read to be slept through. No meditation, no "
     "breathing exercises, no streak, no sleep score, no feed to scroll at bedtime. Their "
     "sleep content is largely fiction and guided relaxation; ours is real material, told in "
     "order. They cost $14.99 and $12.99 a month respectively on the US App Store (checked "
     "September 7, 2026); Lullable is free to download with one story free in full."),

    ("Why not just put on a podcast or an audiobook?",
     "Because both are built to keep you listening, and at midnight that is the wrong goal. A "
     "podcast has two people interrupting each other, laughter, a level jump into an ad read, "
     "and a host whose job is to bring you back next week. An audiobook has a plot that "
     "punishes you for drifting. Lullable is engineered the other way: one voice, no second "
     "speaker, no jeopardy, the level dropping across the episode, and a last thirty seconds "
     "that fade to silence. Anything made to hold attention is the wrong tool for losing it."),

    ("Is a sleep story better than white noise or rain sounds?",
     "It is a different job, and which one fits depends on what is keeping you up. Noise masks "
     "the room — traffic, a partner, a thin wall — but it gives a busy mind nothing "
     "to do, which is why some people lie there listening to rain and thinking anyway. A story "
     "occupies the part of the mind that is narrating. If the problem is the street outside, "
     "use white noise. If the problem is your own commentary, a story is the better tool, and "
     "there is nothing stopping you running both."),

    ("Will it work if meditation has never worked for me?",
     "That is exactly who it is built for. Meditation asks you to empty your mind and to "
     "notice, without judgement, each time it wanders — which, to a mind already racing, "
     "is one more task to be bad at, at midnight. Lullable asks nothing of you. You press play "
     "and somebody explains how a cathedral was built. There is no practice to fail at, no "
     "breath to count, no wandering to catch."),

    ("Do I actually learn anything if I sleep through it?",
     "You keep whatever you were awake for, which is usually the first ten minutes, and the "
     "morning screen shows you the last line you heard so that part is not lost. This is the "
     "point of the category: everything in Lullable is true — marine snow, the standard "
     "railway gauge, the weather at the bottom of the sea — so the stretch you stay "
     "awake for is worth having, and the stretch you sleep through is not a plot you now have "
     "to go back for."),

    ("Who is Lullable for, and who is it not for?",
     "It is for adults who cannot switch off at night: overthinkers, 3am wakers, people who "
     "have tried a meditation app and bounced off it, people who used to fall asleep to "
     "documentaries. It is written for grown-up attention — no fairytales, no baby "
     "voices. It is not a children’s app, not a medical device and not a treatment for "
     "insomnia, and it does not claim to be one. If you have clinical insomnia, see a doctor."),
]

FAQ_CTA_LINE = ("Lullable is on the App Store — free to download, with one 40-minute story "
                "free in full, so you can test it on your own pillow tonight.")
FAQ_CTA_NOTE = ('Not tonight? The Sunday letter is three quiet paragraphs of history or physics, '
                'once a week — <a href="/#signup">join it here</a>.')


def build_faq_page(lang="en"):
    """Writes /faq/ — the ten questions a stranger asks, each answered standalone."""
    t = lambda s: tr(s, lang)
    other = "es" if lang == "en" else "en"
    path = site_path(lang, "/faq/")
    out = ROOT / path.strip("/"); out.mkdir(parents=True, exist_ok=True)
    url = f"{SITE}{path}"
    facts = spanish_facts(spanish.FAQ_FACTS) if lang == "es" else FAQ_FACTS

    def col(items):
        return ('<div class="faq-col">'
                + "".join(f"<details><summary>{html.escape(q)}</summary>"
                          f'<p class="a">{a}</p></details>' for q, a in items)
                + "</div>")
    half = (len(facts) + 1) // 2
    qa = col(facts[:half]) + col(facts[half:])
    body = f'''<article>
<div class="post-head faq-head"><p class="eyebrow">{t("Questions")}</p>
<h1>{t("Lullable, answered")}</h1>
<p class="faq-lead">{t("An iPhone app of {catalogue} long-form true stories for adults, read slowly and engineered to be slept through rather than finished. Free to download, one 40-minute story free in full, not a medical device.").format(catalogue=CATALOGUE_SIZE)}</p></div>
<div class="faq-list">
{qa}
</div>
<p class="post-meta faq-foot">{t('Open any question for the full answer. Looking for the feature detail — timer lengths, narrators, lock screen? That is all on <a href="{app}">what the app actually does</a>. Last updated').format(app=site_path(lang, "/app/"))} <time datetime="{date.today()}">{pretty(str(date.today()), lang)}</time>.</p>
{post_cta(t(FAQ_CTA_LINE), t(FAQ_CTA_NOTE), lang)}
</article>'''

    schemas = [
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer", "text": plain(a)}}
                        for q, a in facts]},
        {"@context": "https://schema.org", **app_schema_node(
            description=t("Long-form true sleep stories for adults, read slowly and fading to silence."))},
    ]
    (out / "index.html").write_text(page(
        t("Lullable FAQ — how the sleep-story app works, and what it costs"),
        t("How does Lullable work? Why does a story quiet a racing mind? What does it cost, and "
          "how is it different from Calm, a podcast or rain sounds? Ten questions, answered."),
        url, body, jsonld(schemas) + FAQ_CSS, lang=lang, alt=f"{SITE}{site_path(other, '/faq/')}"))
    print(f"built {path} ({len(facts)} answered questions + FAQPage schema)")
    return url


# ---------------------------------------------------------------- build

def build():
    warnings = []
    posts = sorted((parse(p) for p in sorted((ROOT / "posts").glob("*.md"))),
                   key=lambda p: p["date"], reverse=True)
    stories = sorted((parse_story(p) for p in sorted((ROOT / "catalog").glob("*.md"))),
                     key=lambda s: s.get("date", ""), reverse=True)
    # The Spanish story pages. catalog/es/<slug>.md holds only what changes in
    # Spanish — the blurb and the body. Every fact (title, narrator, minutes,
    # colours, the sample, which is a line of the English recording) comes from
    # the English file, so the two pages can never disagree about the story. A
    # story with no Spanish file has no Spanish page, and its English page no
    # hreflang.
    es_files = {p.stem: parse_story(p) for p in sorted((ROOT / "catalog" / "es").glob("*.md"))}
    stories_es = [{**s, **{k: v for k, v in es_files[s["slug"]].items() if k != "path"},
                   "path": f"es/{s['path']}"} for s in stories if s["slug"] in es_files]
    for slug in sorted(es_files.keys() - {s["slug"] for s in stories}):
        warnings.append(f"catalog/es/{slug}.md: no English catalog/{slug}.md, so no page")

    # gate first, write nothing on failure
    failures = []
    for p in posts:
        for e in validate_post(p, warnings):
            failures.append(f"{p['path']}: {e}")
    for s in stories + stories_es:
        for e in validate_story(s, warnings):
            failures.append(f"{s['path']}: {e}")
    failures += duplicate_titles(posts)
    warnings += [f"prices.json: {w}" for w in known_prices()[1]]
    if failures:
        print("BUILD ABORTED — fix these before anything is written:")
        for f in failures: print("  HARD FAIL", f)
        sys.exit(1)
    for w in warnings:
        print("  warn:", w)

    (ROOT / "sleep").mkdir(exist_ok=True)
    (ROOT / "stories").mkdir(exist_ok=True)   # generated pages; sources live in catalog/

    # Every section below is written once per language. A page links only to
    # pages in its own language, so a Spanish reader is never sent into English
    # mid-browse without being told.
    LANGS = ("en", "es")
    lang_of = lambda p: p.get("lang", "en")
    posts_in = {lang: [p for p in posts if lang_of(p) == lang] for lang in LANGS}
    stories_in = {"en": stories, "es": stories_es}
    post_url = lambda p: SITE + site_path(lang_of(p), f"/sleep/{p['slug']}/")

    # ---- posts. A `lang: es` post is published under /es/sleep/. Posts are
    # written in one language each, not translated, so a post has no twin.
    for p in posts:
        lang = lang_of(p)
        t = lambda s: tr(s, lang)
        url = post_url(p)
        schemas = [{
            "@context": "https://schema.org", "@type": "Article",
            "headline": p["title"], "description": p["description"],
            "datePublished": p["date"], "mainEntityOfPage": url,
            "inLanguage": HREFLANG[lang],
            "author": {"@type": "Organization", "name": BRAND, "url": SITE},
        }]
        if p.get("question"):
            schemas.append({
                "@context": "https://schema.org", "@type": "FAQPage",
                "mainEntity": [{"@type": "Question", "name": p["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": first_paragraph(p["body"])}}]})
        rel = [(site_path(lang, f"/sleep/{o['slug']}/"), o["title"], t("essay"), "")
               for o in posts_in[lang] if o["slug"] != p["slug"]][:2]
        rel += [(site_path(lang, f"/stories/{s['slug']}/"), s["title"],
                 t("story · {mins} min").format(mins=s["mins"]), story_cover(s))
                for s in stories_in[lang][:2]]
        rendered = md(p["body"])
        # question posts: the first paragraph becomes "the short answer" card —
        # the block skimmers read and AI assistants quote
        if p.get("question"):
            rendered = re.sub(
                r"^<p>(.*?)</p>", lambda m:
                f'<div class="answer"><div class="lbl">{t("The short answer")}</div><p>{m.group(1)}</p></div>',
                rendered, count=1, flags=re.S)
        kind = t({"question": "A question, answered", "definition": "A definition",
                  "fact-world": "A quiet fact-world"}.get(p.get("type", ""), "Essay"))
        head_band = (f'<div class="post-head"><p class="eyebrow">{t("The Sleep Library")} · {kind}</p>'
                     f"<h1>{html.escape(p['title'])}</h1>"
                     f'<p class="post-meta"><time datetime="{p["date"]}">{pretty(p["date"], lang)}</time>'
                     f" · <b>{read_minutes(p['body'])} {t('min read')}</b></p></div>")
        cta = post_cta(note=spanish.AUDIO_NOTE if lang == "es" else None, lang=lang)
        body = (f"<article>\n{head_band}\n<div class=\"measure\">\n{rendered}\n"
                f"{sources_html(p, lang)}{cta}\n</div>"
                f"\n{related_html(rel, lang)}\n</article>")
        out = ROOT / url[len(SITE):].strip("/")
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(page(f"{p['title']} — {BRAND}", p["description"], url, body,
                                             jsonld(schemas), lang=lang))

    # ---- blog index: card grid, one per language
    kinds = {"question": "Question", "definition": "Definition", "fact-world": "Fact-world"}
    for lang in LANGS:
        t = lambda s: tr(s, lang)
        other = "es" if lang == "en" else "en"
        items = "".join(
            f'<li class="idx-card"><div class="row">'
            f'<span class="chip">{t(kinds.get(p.get("type",""), "Essay"))}</span>'
            f'<time datetime="{p["date"]}">{pretty(p["date"], lang)} · {read_minutes(p["body"])} min</time></div>'
            f'<a href="{post_url(p)[len(SITE):]}">{html.escape(p["title"])}</a>'
            f'<p>{html.escape(p["description"])}</p></li>' for p in posts_in[lang])
        body = (f'<div class="idx-head"><p class="eyebrow">{t("The Sleep Library")}</p>'
                f"<h1>{t('Quiet, true things to read at night.')}</h1>"
                f'<p class="post-meta">{t("A new one most days. Nothing urgent, ever.")}</p></div>'
                f'<ul class="idx-grid">{items}</ul>')
        path = site_path(lang, "/sleep/")
        (ROOT / path.strip("/")).mkdir(parents=True, exist_ok=True)
        (ROOT / path.strip("/") / "index.html").write_text(
            page(f"{t('The Sleep Library')} — {BRAND}", t("Quiet, true essays on sleep, racing minds, and pleasantly "
                 "uneventful knowledge. From Lullable, the low-arousal knowledge engine."), f"{SITE}{path}", body,
                 lang=lang, alt=f"{SITE}{site_path(other, '/sleep/')}"))

    # ---- story pages (the per-upload landing pages)
    for lang in LANGS:
        t = lambda s: tr(s, lang)
        other = "es" if lang == "en" else "en"
        twins = {s["slug"] for s in stories_in[other]}
        for s in stories_in[lang]:
            url = f"{SITE}{site_path(lang, f'/stories/{s['slug']}/')}"
            out = ROOT / url[len(SITE):].strip("/")
            out.mkdir(parents=True, exist_ok=True)
            has_card = story_card(s, out, lang)
            og = f"{url}og.png" if has_card else f"{SITE}/og.png"
            schemas = [{
                "@context": "https://schema.org", "@type": "AudioObject",
                "name": s["title"], "description": s["blurb"],
                # the recording is English on both pages; only the page is translated
                "duration": f"PT{s['mins']}M", "inLanguage": "en",
                "isAccessibleForFree": s.get("premium", "true") == "false",
                "author": {"@type": "Organization", "name": BRAND, "url": SITE},
            }, {
                "@context": "https://schema.org", "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": t("Stories"),
                     "item": f"{SITE}{site_path(lang, '/stories/')}"},
                    {"@type": "ListItem", "position": 2, "name": s["title"], "item": url}]}]
            head = jsonld(schemas)
            chips = (f'<div class="chips"><span class="chip amber">▶ {s["mins"]} min</span>'
                     f'<span class="chip">{html.escape(s["genre"])}</span>'
                     f'<span class="chip">{html.escape(s["mood"])}</span>'
                     f'<span class="chip">{t("read by {narrator}").format(narrator=html.escape(s["narrator"]))}</span>'
                     + ('' if s.get("premium") == "false" else '<span class="chip">Premium</span>')
                     + (f'<span class="chip">{spanish.AUDIO_CHIP}</span>' if lang == "es" else "")
                     + '</div>')
            siblings = [(site_path(lang, f"/stories/{o['slug']}/"), o["title"], f"{o['mins']} min · {o['genre']}",
                         story_cover(o)) for o in stories_in[lang] if o["slug"] != s["slug"]][:3]
            essays = [(post_url(p)[len(SITE):], p["title"], t("essay"), "") for p in posts_in[lang][:2]]
            sample = (f'<blockquote>“{html.escape(s["sample"].strip())}”</blockquote>'
                      f'<p class="meta" style="margin-top:-.5rem">{t("The kind of sentence people fall asleep during")}</p>')
            head_band = (f'<div class="post-head"><div class="hero-cover">{story_cover(s, "200px")}</div>'
                         f'<p class="eyebrow">{t("A Lullable sleep story")}</p>'
                         f"<h1>{html.escape(s['title'])}</h1>{chips}</div>")
            body = (f"<article>\n{head_band}\n<div class=\"measure\">\n"
                    f"{md(s['body'])}\n{sample}\n{story_cta(s, lang)}\n</div>\n"
                    f"{related_html(siblings + essays, lang)}\n</article>")
            title = t("{title} — a {mins}-minute sleep story").format(title=s["title"], mins=s["mins"])
            alt = f"{SITE}{site_path(other, f'/stories/{s['slug']}/')}" if s["slug"] in twins else None
            (out / "index.html").write_text(page(f"{title} — {BRAND}", s["blurb"], url, body, head,
                                                 og_image=og, lang=lang, alt=alt))

    # ---- hub pages (the facets)
    # Templated, and deliberately almost none. The risk here is not Google's
    # scaled-content rule — a page a day is three orders of magnitude below the
    # sites that get hit — it is the DOORWAY rule: "substantially similar pages
    # positioned closer to search results than a clear browseable hierarchy."
    # With six stories, nearly every facet anyone would think of lists one item,
    # which is that exact shape, and a body of thin pages drags the essays that
    # already work down with it. So the guard is structural, like the 404-proof
    # interlinking: a facet that cannot list MIN_FACET_ITEMS is not written.
    #
    # Duration buckets (/stories/30-minute/ and siblings) are ABSENT on purpose.
    # They carry the deepest verified demand found in the 2026-09-01 keyword
    # research — 10/10 autocomplete slots — and five of six stories are 39-41
    # minutes, so every bucket but one would be empty. That is an instruction to
    # the recording schedule, not to this generator. Add them when the inventory
    # exists and this loop will pick them up.
    MIN_FACET_ITEMS = 3
    hubs = [
        ("boring-true-stories-to-read", "To read",
         "Boring true stories to read yourself to sleep",
         "Boring true stories to read yourself to sleep.",
         "True stories dull enough to fall asleep during, written out in full so you can read "
         "them instead of listening. Endings given away in the first line.",
         lambda st: True,
         "Every story in the Lullable app is written before it is read aloud, and the written "
         "version is on this site in full. That is unusual enough to say plainly: most sleep "
         "audio exists only as audio, so if you would rather read yourself to sleep than put "
         "something in your ears, the catalogue is mostly closed to you.\n\n"
         "These are not fiction. A Roman bathhouse at the hour the fires go out, the museum of "
         "things that have drifted to the floor of the sea, the eleven-year argument about the "
         "width of a wooden pallet. The material is true, and it is chosen for being genuinely "
         "interesting and entirely inconsequential — nothing here resolves, nothing is at stake, "
         "and nobody is waiting for you to find out what happens.\n\n"
         "Each one gives its ending away in the first minute. That is the whole mechanism: a "
         "story you already know the end of is a story you are permitted to stop reading. "
         "Reading in bed usually fails because the book is trying to keep you there. These are "
         "trying to lose you.\n\n"
         "If you would rather be read to, the same stories are narrated in the app — "
         "[in a male voice](/stories/male-voice/) or a female one."),
        ("male-voice", "Male voice",
         "Sleep stories read in a male voice",
         "Sleep stories read in a male voice.",
         "The Lullable stories narrated by David, Arthur, Brian and Patrick — low, unhurried, and "
         "quieter with every minute. Full text on each page.",
         lambda st: st.get("voice") == "male",
         "Which voice puts you under is not a preference anyone can argue you out of, and it is "
         "one of the few things about sleep audio worth choosing deliberately. Some people need "
         "a lower register to stop tracking the words; others find exactly that too close to a "
         "voice reading them the news.\n\n"
         "These are the stories read by David from Oxford, Arthur from Ludlow, Brian from St Ives and Patrick from "
         "Block Island. What they have in common is not pitch but pacing: no performance, no "
         "characters, no leaning on a word to tell you it matters. The delivery flattens rather "
         "than dramatises, and the last third of every recording is quieter and slower than the "
         "first, on purpose, whether or not you are still awake to notice.\n\n"
         "If none of them work, every one of them is [written out in full to read](/stories/boring-true-stories-to-read/) "
         "if you would rather not listen at all. There are no ads and no music in any of them."),
        ("female-voice", "Female voice",
         "Sleep stories read in a female voice",
         "Sleep stories read in a female voice.",
         "The Lullable stories narrated by Amy and Niamh — warm, flat, and quieter with "
         "every minute. Full text on each page.",
         lambda st: st.get("voice") == "female",
         "Which voice puts you under is not a preference anyone can argue you out of, and it is "
         "one of the few things about sleep audio worth choosing deliberately. Some listeners "
         "settle faster to a higher register; others find it carries too much brightness into a "
         "dark room.\n\n"
         "These are the stories read by Amy from Greenwich and Niamh from "
         "Kinsale. What they have in common is not pitch but pacing: no performance, no "
         "characters, no leaning on a word to tell you it matters. The delivery flattens rather "
         "than dramatises, and the last third of every recording is quieter and slower than the "
         "first, on purpose, whether or not you are still awake to notice.\n\n"
         "If none of them work, the same catalogue [read in a male voice](/stories/male-voice/) "
         "is one page over, and every one of them is [written out in full to read](/stories/boring-true-stories-to-read/) "
         "if you would rather not listen at all. There are no ads and no music in any of them."),
    ]
    hub_urls, hub_nav_items = [], {lang: [] for lang in LANGS}
    for lang in LANGS:
        t = lambda s: tr(s, lang)
        other = "es" if lang == "en" else "en"
        for slug, nav, title, h1, desc, keep, intro in hubs:
            picked = [st for st in stories_in[lang] if keep(st)]
            if len(picked) < MIN_FACET_ITEMS:
                print(f"  skip {site_path(lang, f'/stories/{slug}/')} — {len(picked)} stories, needs {MIN_FACET_ITEMS}")
                continue
            if lang == "es":   # same facet, same stories; only the words change
                nav, title, h1, desc, intro = spanish.HUBS[slug]
            url = f"{SITE}{site_path(lang, f'/stories/{slug}/')}"
            cards = "".join(
                f'<li class="idx-card">{story_cover(st, "104px")}'
                f'<div class="row"><span class="chip amber">▶ {st["mins"]} min</span>'
                f'<span class="sub">{html.escape(st["genre"])} · {html.escape(st["narrator"])}</span></div>'
                f'<a href="{site_path(lang, "/stories/" + st["slug"] + "/")}">{html.escape(st["title"])}</a>'
                f'<p>{html.escape(st["blurb"])}</p></li>' for st in picked)
            essays = [(post_url(q)[len(SITE):], q["title"], t("essay"), "") for q in posts_in[lang][:2]]
            body = (f'<div class="idx-head"><p class="eyebrow">{t("Stories")}</p><h1>{html.escape(h1)}</h1>'
                    f'<p class="post-meta">{t("{n} stories · endings given away").format(n=len(picked))}</p></div>'
                    f'<article><div class="measure">{md(intro)}</div></article>'
                    f'<ul class="idx-grid">{cards}</ul>'
                    f'{related_html(essays, lang)}')
            schemas = [{
                "@context": "https://schema.org", "@type": "CollectionPage",
                "name": title, "description": desc, "url": url,
            }, {
                "@context": "https://schema.org", "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": t("Stories"),
                     "item": f"{SITE}{site_path(lang, '/stories/')}"},
                    {"@type": "ListItem", "position": 2, "name": h1.rstrip("."), "item": url}]}]
            out = ROOT / url[len(SITE):].strip("/")
            out.mkdir(parents=True, exist_ok=True)
            twin = len([st for st in stories_in[other] if keep(st)]) >= MIN_FACET_ITEMS
            alt = f"{SITE}{site_path(other, f'/stories/{slug}/')}" if twin else None
            (out / "index.html").write_text(page(f"{title} — {BRAND}", desc, url, body, jsonld(schemas),
                                                 lang=lang, alt=alt))
            hub_urls.append(url)
            hub_nav_items[lang].append((url, nav))

    # ---- stories index: card grid with gradient covers
    for lang in LANGS:
        t = lambda s: tr(s, lang)
        other = "es" if lang == "en" else "en"
        items = "".join(
            f'<li class="idx-card">{story_cover(s, "104px")}'
            f'<div class="row"><span class="chip amber">▶ {s["mins"]} min</span>'
            f'<span class="sub">{html.escape(s["genre"])} · {html.escape(s["narrator"])}</span></div>'
            f'<a href="{site_path(lang, "/stories/" + s["slug"] + "/")}">{html.escape(s["title"])}</a>'
            f'<p>{html.escape(s["blurb"])}</p></li>' for s in stories_in[lang])
        hub_nav = ("".join(f'<a class="chip" href="{u[len(SITE):]}">{n}</a>' for u, n in hub_nav_items[lang])
                   if hub_nav_items[lang] else "")
        body = (f'<div class="idx-head"><p class="eyebrow">{t("Stories")}</p>'
                f"<h1>{t('Every story in the app.')}</h1>"
                f'<p class="post-meta">{t("Endings given away, nothing withheld.")}</p>'
                f'<div class="chips" style="justify-content:center;margin-top:1.25rem">{hub_nav}</div></div>'
                f'<ul class="idx-grid">{items}</ul>')
        path = site_path(lang, "/stories/")
        (ROOT / path.strip("/")).mkdir(parents=True, exist_ok=True)
        (ROOT / path.strip("/") / "index.html").write_text(
            page(f"{t('Sleep stories')} — {BRAND}", t("Every sleep story in the Lullable app: slow fiction, nature and "
                 "weather, folklore — read warmly and quieter every minute."), f"{SITE}{path}", body,
                 lang=lang, alt=f"{SITE}{site_path(other, '/stories/')}"))

    # ---- standing pages (/privacy/, /terms/, /support/) — same claim gate as
    # the essays, since "not a medical device" is the one sentence we cannot
    # get wrong. Anything dropped in legal/*.md becomes /<filename>/, and its
    # Spanish twin in legal/es/ becomes /es/<filename>/.
    legal = {"en": [parse_story(p) for p in sorted((ROOT / "legal").glob("*.md"))],
             "es": [{**parse_story(p), "path": f"es/{p.name}"}
                    for p in sorted((ROOT / "legal" / "es").glob("*.md"))]}
    for lang in LANGS:
        t = lambda s: tr(s, lang)
        other = "es" if lang == "en" else "en"
        twins = {l["slug"] for l in legal[other]}
        for l in legal[lang]:
            hits = prohibited_claims_in(l["body"])
            if hits:
                sys.exit(f"HARD FAIL {l['path']}: prohibited claim(s) {hits}")
            url = f"{SITE}{site_path(lang, f'/{l['slug']}/')}"
            out = ROOT / url[len(SITE):].strip("/")
            out.mkdir(parents=True, exist_ok=True)
            # A page with a `tagline:` is a pitch, not a document: the sub-headline
            # replaces "Last updated". `cta:` + `cta_href:` put the one action under
            # the headline and again at the end, so it is the most obvious thing on
            # the page at both places a reader decides.
            meta_line = (html.escape(l["tagline"]) if l.get("tagline") else
                         f'{t("Last updated")} <time datetime="{l["updated"]}">{pretty(l["updated"], lang)}</time>')
            head_band = (f'<div class="post-head"><p class="eyebrow">{BRAND}</p>'
                         f"<h1>{html.escape(l['title'])}</h1>"
                         f'<p class="post-meta{" tagline" if l.get("tagline") else ""}">{meta_line}</p></div>')
            cta_top = cta_end = ""
            if l.get("cta") and l.get("cta_href"):
                button = (f'<a href="{html.escape(l["cta_href"], quote=True)}">{html.escape(l["cta"])}</a>')
                note = f'<p class="cta-note">{inline(l["cta_note"])}</p>' if l.get("cta_note") else ""
                cta_top = f'<div class="cta cta-top">{button}{note}</div>\n'
                cta_end = f'<div class="cta">{button}{note}</div>\n'
            text = l["body"].replace("{{launch}}", launch_copy(lang))
            body = (f'<article>\n{head_band}\n{cta_top}<div class="measure">\n{md(text)}\n'
                    f'{cta_end}</div>\n</article>')
            alt = f"{SITE}{site_path(other, f'/{l['slug']}/')}" if l["slug"] in twins else None
            (out / "index.html").write_text(page(f"{l['title']} — {BRAND}", l["description"], url, body,
                                                 lang=lang, alt=alt))

    chrono_urls = build_chronotype() + build_chronotype("es")
    app_urls = [build_app_page(), build_app_page("es")]
    faq_urls = [build_faq_page(), build_faq_page("es")]

    sync_go_rules()

    # ---- sitemap / rss / robots / llms
    # English first, in the order it has always had, then Spanish. A URL whose
    # twin exists in the other language lists both, and x-default is English.
    def lang_urls(lang):
        s = lambda path: f"{SITE}{site_path(lang, path)}"
        mine = lambda us: [u for u in us if u.startswith(f"{SITE}/es/") == (lang == "es")]
        return ([s("/"), s("/manifesto/"), s("/press/"), s("/sleep/"), s("/stories/")]
                + mine(app_urls + faq_urls) + mine(chrono_urls)
                + [s(f"/{l['slug']}/") for l in legal[lang]]
                + [post_url(p) for p in posts_in[lang]]
                + [s(f"/stories/{st['slug']}/") for st in stories_in[lang]]
                + mine(hub_urls))
    urls = lang_urls("en") + lang_urls("es")
    have = set(urls)

    def sitemap_entry(u):
        path = u[len(SITE):]
        twin = SITE + (path[3:] if path.startswith("/es/") else "/es" + path)
        if twin not in have:
            return f"<url><loc>{u}</loc></url>"
        en, es = (twin, u) if path.startswith("/es/") else (u, twin)
        return (f'<url><loc>{u}</loc>'
                f'<xhtml:link rel="alternate" hreflang="en" href="{en}"/>'
                f'<xhtml:link rel="alternate" hreflang="es-MX" href="{es}"/>'
                f'<xhtml:link rel="alternate" hreflang="es" href="{es}"/>'
                f'<xhtml:link rel="alternate" hreflang="x-default" href="{en}"/></url>')
    sm = "\n".join(sitemap_entry(u) for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        f'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n{sm}\n</urlset>')

    # The feed is the English Sleep Library, so it carries English posts only.
    rss_items = "".join(
        f"<item><title>{html.escape(p['title'])}</title>"
        f"<link>{SITE}/sleep/{p['slug']}/</link><guid>{SITE}/sleep/{p['slug']}/</guid>"
        f"<pubDate>{datetime.strptime(p['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc).strftime('%a, %d %b %Y 21:00:00 GMT')}</pubDate>"
        f"<description>{html.escape(p['description'])}</description></item>" for p in posts_in["en"])
    (ROOT / "rss.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
        f"<title>{BRAND} — The Sleep Library</title><link>{SITE}/sleep/</link>"
        f"<description>Quiet, true things to read at night.</description>{rss_items}</channel></rss>")

    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")

    post_lines = "\n".join(f"- [{p['title']}]({post_url(p)}): {p['description']}" for p in posts)
    story_lines = "\n".join(f"- [{s['title']}]({SITE}/stories/{s['slug']}/): {s['mins']}-minute "
                            f"{s['genre'].lower()} sleep story. {s['blurb']}" for s in stories)
    (ROOT / "llms.txt").write_text(
        f"# {BRAND}\n\n> {BRAND} is the low-arousal knowledge engine: an audio app that reads "
        f"sleep stories and true, gently fascinating material in a warm, flat, progressively "
        f"quieter voice, engineered so listeners fall asleep mid-sentence. It is the alternative "
        f"to meditation apps for people whose racing minds cannot be emptied, only occupied. "
        f"Not a medical device.\n\n"
        f"## Key pages\n- [Home]({SITE}/): what Lullable is, with an audio sample\n"
        f"- [The Sleep Library]({SITE}/sleep/): essays on sleep and pleasantly uneventful knowledge\n"
        f"- [Stories]({SITE}/stories/): every sleep story in the app\n"
        f"- [Chronotype quiz]({SITE}/chronotype/): five questions, one of five sleep animals (blackbird to octopus)\n\n"
        f"- [What the app does]({SITE}/app/): every feature question, answered in one sentence\n\n"
        f"- [FAQ]({SITE}/faq/): how it works, what it costs, and how it differs from Calm, podcasts and white noise\n\n"
f"- [Creators]({SITE}/creators/): the creator and podcast partner program — one link, paid per download the App Store attributes to it\n\n"
        f"- [En español]({SITE}/es/): the whole site in Mexican Spanish. The app and its stories are in English.\n\n"
        + "## What Lullable does\n"
        + "".join(f"- **{q}** {plain(a)}\n" for q, a in APP_FACTS) + "\n"

        + "## Common questions\n"
        + "".join(f"- **{q}** {plain(a)}\n" for q, a in FAQ_FACTS) + "\n"

        f"## Essays\n{post_lines}\n\n## Stories\n{story_lines}\n\n"
        f"## Elsewhere\n"
        f"- [Instagram](https://www.instagram.com/getlullable/): the nightly fact cards\n"
        f"- [TikTok](https://www.tiktok.com/@getlullable): the same cards, in motion\n"
        f"- [YouTube](https://www.youtube.com/@lullableapp): full-length sleep stories to listen to\n"
        f"- [Facebook](https://www.facebook.com/profile.php?id=61594011460380): the same nightly cards\n\n"
        f"## About\n- Published by Tecnologías Stellar, S.A. de C.V. (Mexico City), "
        f"built by stellartech.xyz. Contact: info@getlullable.com\n")

    print(f"built {len(posts)} posts + {len(stories)} story pages ({len(stories_es)} in Spanish) "
          f"-> sleep/ stories/ es/ + sitemap + rss + robots + llms.txt")

# ---------------------------------------------------------------- scaffolds

def scaffold_post(slug, topic=None):
    slug = re.sub(r"[^a-z0-9-]", "", slug.lower().replace(" ", "-"))
    path = ROOT / "posts" / f"{date.today().isoformat()}-{slug}.md"
    if path.exists():
        sys.exit(f"{path.name} already exists")
    t = topic or {}
    lang_line = f"lang: {t['lang']}\n" if t.get("lang") else ""
    q = f"question: {t.get('title', 'Optional — the search question this answers. Delete if none.')}\n" \
        if (t.get("type") == "question" or not topic) else ""
    path.write_text(f"""---
title: {t.get('title', 'TITLE')}
description: Meta description under 155 characters.
{lang_line}
{q}type: {t.get('type', 'question | definition | fact-world')}
---

First paragraph: answer plainly in two or three sentences. This paragraph is what
search engines and AI assistants will quote, so it must stand alone.
{('Angle: ' + t['angle']) if t.get('angle') else ''}
{('Keywords to weave in naturally: ' + ', '.join(t['keywords'])) if t.get('keywords') else ''}

## A section

More.
""")
    print(f"created {path.relative_to(ROOT)}")
    if topic:
        print(f"brief: type={t['type']}  angle={t.get('angle','—')}  keywords={', '.join(t.get('keywords', []))}")

def next_topic():
    data = json.loads((ROOT / "topics.json").read_text())
    published = {parse(p)["slug"]: parse(p).get("type", "") for p in (ROOT / "posts").glob("*.md")}
    last_type = ""
    if published:
        # tie-break by mtime: on catch-up days several posts share a date, and
        # glob order is filesystem-dependent — without this the rotation rule
        # silently compared against an arbitrary one of them (found 2026-08-12).
        newest = max((ROOT / "posts").glob("*.md"),
                     key=lambda p: (p.stem[:10], p.stat().st_mtime))
        last_type = parse(newest).get("type", "")
    # A topic can carry "blocked": "<reason>" to stay in the queue but out of
    # rotation. Added 2026-09-10 for sleep-app-that-picks-for-you, whose angle
    # is a claim about a feature that has not shipped — the unattended drafter
    # would have written it as true. Any truthy value skips; the string is the
    # reason a human reads later.
    pending = [t for t in data["topics"]
               if t["slug"] not in published and not t.get("blocked")]
    if not pending:
        sys.exit("queue is empty — add topics to topics.json")
    pick = next((t for t in pending if t["type"] != last_type), pending[0])
    scaffold_post(pick["slug"], pick)

def scaffold_story(slug):
    slug = re.sub(r"[^a-z0-9-]", "", slug.lower().replace(" ", "-"))
    path = ROOT / "catalog" / f"{slug}.md"
    if path.exists():
        sys.exit(f"{path.name} already exists")
    path.write_text(f"""---
title: TITLE
narrator: NAME
voice: male | female
mins: 45
genre: Folklore | Nature & Weather | Slow Fiction | Wandering
mood: Drifting | Weightless | Wandering | Faraway | Hushed | Dreaming
premium: true
date: {date.today().isoformat()}
blurb: One or two sentences, under 200 characters, in the app's card voice.
sample: …a sentence from the story, cut mid-clause, ending with an em-dash—
---

Two short paragraphs introducing the story, in the warm-academic voice.
End the second with "The ending, given away now:" and give it away.

## The first minute

> The opening ~100 words of the story itself, as a block quote.

## Why this one works at night

Two or three sentences on the mechanism — what this story gives a racing mind to hold.
""")
    print(f"created {path.relative_to(ROOT)}")

# ---------------------------------------------------------------- indexnow
# Bing and Yandex accept a push instead of waiting to be crawled, and Bing's
# index is what ChatGPT search reads — so a new essay can be findable in an
# LLM answer the same night instead of next week. Google ignores IndexNow;
# it has Search Console and its own schedule. The key has been sitting in the
# repo unused since launch. This is the two dozen lines that use it.

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def indexnow_key():
    """The key, checked against the copy the search engine will fetch.

    Two files have to agree: .indexnow-key is what we send, and <key>.txt at
    the site root is what they fetch to prove the key is ours. A mismatch is a
    silent no-op at their end — the submission is accepted and then dropped —
    so it is worth two lines here to catch it loudly instead."""
    try:
        key = (ROOT / ".indexnow-key").read_text().strip()
    except OSError:
        print("indexnow: no .indexnow-key file — skipped")
        return None
    if not key:
        print("indexnow: .indexnow-key is empty — skipped")
        return None
    proof = ROOT / f"{key}.txt"
    if not proof.exists() or proof.read_text().strip() != key:
        print(f"indexnow: {key}.txt missing or does not match .indexnow-key — skipped")
        return None
    return key


def page_url(rel):
    """Repo path -> public URL, or None when the file is not a page."""
    if not rel.endswith("index.html"):
        return None
    return f"{SITE}/{rel[:-len('index.html')]}"


def changed_urls(rev="HEAD"):
    """Only the pages that changed in <rev>.

    IndexNow is for telling them what is new. Resubmitting the whole site on
    every deploy is what gets a key throttled, so the commit decides."""
    import subprocess
    try:
        out = subprocess.run(["git", "diff", "--name-only", f"{rev}~1", rev],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except Exception:
        return []
    return sorted({u for u in (page_url(p) for p in out.split()) if u})


def all_urls():
    """Every page on the site — for a manual `ping --all` after a redesign."""
    return sorted({u for u in (page_url(str(p.relative_to(ROOT)))
                               for p in ROOT.rglob("index.html")) if u})


def ping_indexnow(urls):
    """Submit changed URLs. Never fatal — the deploy has already happened.

    Timing is not a worry: they queue the URLs and crawl over the following
    minutes to hours, long after Vercel has finished the ~30s build."""
    import json as _json, urllib.request, urllib.error
    key = indexnow_key()
    if not key:
        return
    if not urls:
        print("indexnow: no pages changed in this commit — nothing to submit")
        return
    payload = {"host": SITE.split("//")[1], "key": key,
               "keyLocation": f"{SITE}/{key}.txt", "urlList": urls[:10000]}
    req = urllib.request.Request(
        INDEXNOW_ENDPOINT, data=_json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        print(f"indexnow: endpoint unreachable ({str(e)[:60]}) — skipped, deploy is fine")
        return
    ok = code in (200, 202)                      # 202 = accepted, key check pending
    print(f"indexnow: {'submitted' if ok else 'REFUSED'} {len(urls)} url(s) (HTTP {code})")
    for u in urls:
        print(f"  {u}")
    if not ok:
        print("  403 = key file not fetchable, 422 = key/host mismatch, 429 = throttled.")


def cmd_ping(everything=False):
    """Manual submit, for when a deploy happened outside `ship`."""
    ping_indexnow(all_urls() if everything else changed_urls())


def ship(message):
    """Build, commit, rebase, push. That is the entire deploy.

    Vercel's GitHub integration owns getlullable.com and builds `main` to
    production on every push — there is no CLI to install, no dashboard to
    visit, and `vercel deploy` would create a SECOND, domain-less project.
    The build runs first so a failed claim gate stops the push, not the site."""
    import subprocess
    build()
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    if subprocess.run(["git", "commit", "-m", message], cwd=ROOT).returncode:
        print("nothing new to commit — pushing whatever is already committed")
    # Rebase before pushing. 2026-08-15: the daily post was committed, then the
    # push was rejected because an IG-scheduler commit had landed on main from
    # another session. Two loops write this repo, so the remote moving ahead is
    # normal, not an incident. Rebase (never merge) keeps main a straight line.
    # A conflict here stops the deploy on purpose — resolve it by hand.
    subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=ROOT, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=True)
    print(f"pushed. vercel builds main -> production in ~30s: {SITE}")
    ping_indexnow(changed_urls())


# ---------------------------------------------------------------- launch day

def app_cta():
    """The app call-to-action, for every generated page.

    index.html's `APP_STORE_URL` is the single source of truth for whether the
    product is downloadable, so the generated pages read it rather than keeping
    their own copy of the answer. `golive` edits one constant in one file, the
    next build propagates it to /sleep/, /stories/ and the legal pages, and
    there is no second place to forget."""
    try:
        m = re.search(r'var APP_STORE_URL\s*=\s*"([^"]*)"',
                      (ROOT / "index.html").read_text())
        url = m.group(1) if m else ""
    except OSError:
        url = ""
    # Live since 2026-09-21. If index.html is ever unreadable the fallback is the
    # store, not the retired waitlist: a missing file must not un-launch the site.
    return (url or STORE_URL, "Get the app")


# Apple's campaign provider token (the pt= in a campaign link). It exists only
# after the app has been live and downloading for ~24h: App Store Connect ›
# Analytics › Acquisition › Campaigns › (+) shows it. Paste it here on launch
# day + 1, run `python3 build.py`, ship. Until then /go/ links reach the store
# without a token and Apple cannot credit the creator.
APPLE_PT = ""
GO_SOURCE = "/go/:code([a-z0-9-]{2,30})"   # Apple's campaign token is ≤30 chars


def go_rules():
    """The creator links, getlullable.com/go/<code>, as vercel.json redirects.

    One rule while the app is on the waitlist: the code rides along as ?ref=,
    which the signup form already stores in Sender as `source`. After golive,
    iPhones go straight to the App Store with the code as Apple's campaign
    token (ct=), so App Store Connect counts first-time downloads per creator
    with no SDK in the app; everyone else still lands on the homepage, where
    there is a pitch instead of a listing they cannot install. 307, never 308:
    browsers cache a 308 forever and would freeze every creator link on
    whichever destination they saw first."""
    home = {"source": GO_SOURCE, "destination": "/?ref=:code", "permanent": False}
    if not APPLE_PT:
        print("WARNING: APPLE_PT is empty — /go/ links reach the store without a campaign")
        print("         token, so App Store Connect cannot credit creators. Generate the")
        print("         campaign link (Analytics › Acquisition › Campaigns › +) and paste pt.")
    pt = f"pt={APPLE_PT}&" if APPLE_PT else ""
    store = {"source": GO_SOURCE,
             "has": [{"type": "header", "key": "user-agent", "value": ".*(iPhone|iPad|iPod).*"}],
             "destination": f"https://apps.apple.com/app/apple-store/id{APPLE_ID}?{pt}ct=:code&mt=8",
             "permanent": False}
    return [store, home]


def launch_copy(lang="en"):
    """The one paragraph on /creators/ that depends on launch state. The app is
    live, so what is left to vary is whether Apple has issued our campaign tag
    yet — a creator must not be told their link is counting before it is. The
    markdown carries a {{launch}} token; the build substitutes the truth."""
    if not APPLE_PT:
        return tr("The app is on the App Store. Your link sends iPhones straight to the listing and "
                  "everyone else to our site. Apple issues our campaign tag a day or two after launch, "
                  "and downloads made before it exists cannot be tied to a code — so wait for our "
                  "email confirming your link is tagged before you push. Then go.", lang)
    return tr("The app is on the App Store. Your link sends iPhones straight to the listing with "
              "your tag attached, and everyone else to our site. Apple counts first-time downloads "
              "per tag from the moment of the tap; there is nothing to wait for.", lang)


def sync_go_rules():
    """Keep vercel.json's /go/ redirects in step with the launch state, the way
    every generated page reads app_cta(): one constant, no second copy."""
    path = ROOT / "vercel.json"
    cfg = json.loads(path.read_text())
    keep = [r for r in cfg.get("redirects", []) if not r["source"].startswith("/go/")]
    cfg["redirects"] = keep + go_rules()
    new = json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"
    if new != path.read_text():
        path.write_text(new)
        print("vercel.json: /go/ creator links updated")


def appstore_status(apple_id=APPLE_ID):
    """Ask Apple whether the app is actually live, in a few storefronts.

    The whole point of the launch-day flip is that it cannot be done early.
    An App Store Connect record exists long before the listing resolves, and a
    CTA pointing at a page that 404s is worse than an honest waitlist — so this
    is a hard gate, not a warning. Read-only, no key, no account."""
    import json as _json, urllib.request, urllib.error
    out = {}
    for cc in ("us", "mx", "gb"):
        url = f"https://itunes.apple.com/lookup?id={apple_id}&country={cc}"
        try:
            with urllib.request.urlopen(url, timeout=8) as r:
                d = _json.loads(r.read().decode())
            out[cc] = d["results"][0] if d.get("resultCount") else None
        except Exception as e:                       # offline, rate-limited, whatever
            out[cc] = {"__error__": str(e)[:60]}
    return out


def cmd_appstore():
    """Read-only: is it live yet, and what would ship if it were?"""
    print(f"App Store Connect record: GetLullable / Apple ID {APPLE_ID}")
    print(f"Candidate URL:            {STORE_URL}\n")
    live = None
    for cc, r in appstore_status().items():
        if r is None:
            print(f"  {cc}: not live")
        elif "__error__" in r:
            print(f"  {cc}: could not check ({r['__error__']})")
        else:
            live = r
            print(f"  {cc}: LIVE — {r.get('trackName')} v{r.get('version')} "
                  f"{r.get('formattedPrice')} — {r.get('trackViewUrl')}")
    print()
    if live:
        print("Ready. Run:  python3 build.py golive")
    else:
        print("Not ready. Every CTA stays on the waitlist, which is the honest state.")
        print("Re-run this after the listing goes live.")
    return 0 if live else 1


def app_schema_node(rec=None, description=None):
    """The homepage's MobileApplication node — the markup that lets Google and
    the answer engines say "iPhone app, free, iOS" instead of guessing.

    It is authored here and emitted only by `golive`, because every field in it
    is a claim that is false until the listing resolves. Where Apple's lookup
    answers a question (version, price, minimum iOS), the answer comes from
    Apple rather than from this file — the point is to have no second copy of a
    fact that Apple owns.

    Two deliberate omissions:
      - No aggregateRating. Inventing one is a manual-action offence at Google
        and there are no real reviews on day one. Add it when the App Store has
        ratings worth quoting, from the lookup, or never.
      - applicationCategory is LifestyleApplication, not HealthApplication.
        The whole site is careful to say this is not a medical device; the
        schema does not get to say otherwise."""
    node = {
        "@type": "MobileApplication",
        "@id": f"{SITE}/#app",
        "name": BRAND,
        "applicationCategory": "LifestyleApplication",
        "operatingSystem": "iOS",
        "url": STORE_URL,
        "installUrl": STORE_URL,
        "publisher": {"@id": f"{SITE}/#org"},
    }
    if description:
        node["description"] = description
    if rec:
        if rec.get("version"):
            node["softwareVersion"] = rec["version"]
        if rec.get("minimumOsVersion"):
            node["operatingSystem"] = f"iOS {rec['minimumOsVersion']}+"
        if rec.get("price") is not None:
            # Apple hands back a float; "0.0" is a valid but sloppy price string.
            price = rec["price"]
            price = str(int(price)) if float(price).is_integer() else f"{float(price):.2f}"
            node["offers"] = {"@type": "Offer",
                              "price": price,
                              "priceCurrency": rec.get("currency", "USD")}
    return node


def insert_app_schema(src, rec=None):
    """Splice the app node into the homepage @graph. Idempotent."""
    if f"{SITE}/#app" in src:
        return src, False
    desc = re.search(r'<meta name="description" content="([^"]*)"', src)
    blob = json.dumps(app_schema_node(rec, desc.group(1) if desc else None),
                      ensure_ascii=False, separators=(",", ":"))
    anchor = '  "inLanguage":"en"}\n]}'
    if anchor not in src:
        print("WARNING: homepage @graph not found in the expected shape — "
              "app schema NOT added. Add it by hand.")
        return src, False
    return src.replace(anchor, '  "inLanguage":"en"},\n ' + blob + '\n]}', 1), True


def cmd_golive(force=False):
    """Flip the whole site from waitlist to download, in one command.

    Three things happen, and all three have to happen together — flipping the
    buttons and leaving the copy saying "be there the night it opens" would be a
    launch-day embarrassment, so the successor strings are authored in the HTML
    now as data-live-text and swapped here.

      1. APP_STORE_URL is set (the JS then rewrites every .app-link at runtime,
         and this rewrite makes the same change statically so crawlers see it);
      2. every element with data-live-text takes its live wording;
      3. the Safari Smart App Banner meta is added;
      4. the MobileApplication schema node joins the homepage @graph, built
         from Apple's own lookup — see app_schema_node().

    Refuses unless Apple says the listing resolves. --force exists for the hour
    between "approved" and "propagated", and prints a loud warning."""
    index = ROOT / "index.html"
    src = index.read_text()
    if 'var APP_STORE_URL = "";' not in src:
        sys.exit("index.html: APP_STORE_URL is already set — nothing to do.")
    # Everything under sleep/, stories/ and the legal pages is generated and picks
    # the new state up from app_cta() on the next build. These two are written by
    # hand, so golive edits them directly.
    HANDWRITTEN = [index, ROOT / "manifesto" / "index.html", ROOT / "press" / "index.html"]

    live = [r for r in appstore_status().values() if r and "__error__" not in r]
    if not live and not force:
        print("REFUSING: Apple's lookup says the listing is not live in us/mx/gb.")
        print("A CTA pointing at a dead store page is worse than a waitlist.")
        print("Check with `python3 build.py appstore`, or `golive --force` if you")
        print("are inside the propagation window and have opened the URL yourself.")
        sys.exit(1)
    if not live:
        print("WARNING: --force used. Apple does not report this app as live.")
        print(f"         Open {STORE_URL} yourself before you push.\n")

    out = src.replace('var APP_STORE_URL = "";', f'var APP_STORE_URL = "{STORE_URL}";', 1)

    # The JS rewrites every .app-link at runtime, which is fine for a person and
    # useless to a crawler on launch day. Do the same edit statically so the
    # served HTML says "Get the app" before a line of script runs.
    def link(m):
        tag, body = m.group("tag"), m.group("body")
        tag = re.sub(r'href="[^"]*"', f'href="{STORE_URL}"', tag)
        live = re.search(r'data-live="([^"]*)"', tag)
        if live:
            body = live.group(1)
            tag = re.sub(r'\s*data-live="[^"]*"', "", tag)
        return tag + ">" + body + "</a>"
    app_link_re = re.compile(
        r'(?P<tag><a\b[^>]*class="[^"]*app-link[^"]*"[^>]*)>(?P<body>.*?)</a>', re.S)
    out, n_links = app_link_re.subn(link, out)

    # the pre-launch strings hand over to the ones authored beside them
    swapped = 0
    def swap(m):
        nonlocal swapped
        swapped += 1
        return m.group("open") + m.group("live") + m.group("close")
    pattern = re.compile(
        r'(?P<open><(?P<tag>[a-z0-9]+)\b[^>]*?)\s+data-live-text="(?P<live>[^"]*)"(?P<rest>[^>]*>)'
        r'(?P<body>.*?)(?P<closetag></(?P=tag)>)', re.S)
    def swap2(m):
        nonlocal swapped
        swapped += 1
        return m.group("open") + m.group("rest") + m.group("live") + m.group("closetag")
    out = pattern.sub(swap2, out)

    # Once the app is downloadable the join form is the newsletter, not the
    # primary action — it gives the filled treatment back to the store CTAs.
    out = out.replace('class="btn solid" id="submit"', 'class="btn" id="submit"', 1)

    # Safari's native banner, which only makes sense once the listing resolves
    banner = f'<meta name="apple-itunes-app" content="app-id={APPLE_ID}">\n'
    out = out.replace('<meta name="color-scheme" content="dark">',
                      '<meta name="color-scheme" content="dark">\n' + banner.rstrip("\n"), 1)

    out, schema_added = insert_app_schema(out, live[0] if live else None)

    index.write_text(out)
    print(f"index.html: APP_STORE_URL set, {swapped} strings swapped to live copy, "
          f"{n_links} CTAs pointed at the store, Smart App Banner added.")
    print(f"index.html: MobileApplication schema {'added' if schema_added else 'NOT added'}"
          f"{' (built from Apple lookup)' if schema_added and live else ''}.")

    for f in HANDWRITTEN[1:]:
        if not f.exists():
            continue
        t = f.read_text()
        n = 0
        t, k = pattern.subn(swap2, t); n += k
        t, k = app_link_re.subn(link, t); n += k
        t2 = t.replace('href="/#signup" data-live-href="STORE"', f'href="{STORE_URL}"')
        n += (t != t2); t = t2
        f.write_text(t)
        print(f"{f.relative_to(ROOT)}: {n} change(s).")

    print("\nGenerated pages (/sleep/, /stories/, /privacy/, /terms/) read the same")
    print("constant via app_cta() — they flip on the next `python3 build.py`.")
    if (ROOT / "assets" / "brand" / "appstore-badge.svg").exists():
        print("assets/brand/appstore-badge.svg found — swap it into the hero button by hand;")
        print("Apple's badge must be used as supplied, unmodified.")
    else:
        print("No Apple badge asset present. The hero button stays plain Lullable type,")
        print("which is allowed; Apple's badge may only be used as the lockup they supply.")
    print("\nNow: python3 build.py  &&  browser-verify  &&  build.py ship \"Launch: get the app\"")
    print("\nCreator links (/go/<code>) flip to the App Store on that build. Then, on day 2:")
    print("  1. App Store Connect › Analytics › Acquisition › Campaigns › (+) — copy the pt=")
    print("     value into APPLE_PT in build.py, `python3 build.py`, ship. Without it Apple")
    print("     cannot credit a creator for a download.")
    print("  2. Launch email button: https://getlullable.com/go/{{ source | default: \"waitlist\" }}")
    print("     (Sender Liquid tag). Test-send once. Apple only credits downloads within 24h")
    print("     of the tap, so this is how pre-launch audiences get credited to their creator.")
    print("  /creators/ rewrites its own launch paragraph on each build (launch_copy()).")
    # The listing going live is also the moment Apple Search Ads becomes usable.
    # You cannot advertise — or read Search Popularity for — an app that is not
    # live, which is why the account opened on 2026-09-01 had nothing to select.
    # Search Popularity (5-100, logarithmic) is the only free App Store volume
    # figure that exists, and every keyword judgement made before launch was
    # competition-shaped and volume-blind. Printed here so it happens once,
    # rather than being remembered.
    print("\nAlso today, now that the listing resolves:")
    print("  searchads.apple.com -> Advanced -> new campaign -> Recommended Keywords")
    print("  Save it as a DRAFT. Never set it live. The popularity scores are")
    print("  visible without spending anything, and they are the only free App")
    print("  Store volume data there is. Pull scores for the open terms before")
    print("  the 30/30/100 metadata is finalised:")
    for k in ("boring stories to sleep", "sleepy history", "history sleep stories",
              "boring history", "true stories to fall asleep", "nonfiction sleep stories",
              "sleep stories for overthinkers", "long sleep stories", "sleep timer",
              "sleep stories for adults", "boring audiobooks for sleep"):
        print(f"    - {k}")
    print("  Keep 'lullaby', 'white noise' and 'sleep sounds' out entirely — the")
    print("  first lands in baby music, the other two are six-figure-rating terms.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "new" and len(args) > 1:
        scaffold_post(args[1])
    elif args and args[0] == "next":
        next_topic()
    elif args and args[0] == "story" and len(args) > 1:
        scaffold_story(args[1])
    elif args and args[0] == "appstore":
        sys.exit(cmd_appstore())
    elif args and args[0] == "golive":
        cmd_golive(force="--force" in args)
    elif args and args[0] == "ping":
        cmd_ping(everything="--all" in args)
    elif args and args[0] == "ship":
        ship(args[1] if len(args) > 1 else f"Site update {date.today().isoformat()}")
    else:
        build()
