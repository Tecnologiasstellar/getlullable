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
import html, json, re, sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "https://getlullable.com"          # <- the one config value
BRAND = "Lullable"

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
]
NEGATORS = ("not ", "n't ", "never ", "no ", "isn't ", "aren't ", "won't ", "without ")

def prohibited_claims_in(text):
    low = text.lower()
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
    if not p.get("type"):
        warnings.append(f"{p['path']}: no type: (question|definition|fact-world) — rotation can't see it")
    return errs

def validate_story(s, warnings):
    errs = []
    for field in ("title", "narrator", "mins", "genre", "mood", "blurb", "sample", "date"):
        if not s.get(field):
            errs.append(f"missing {field}")
    if not str(s.get("mins", "")).isdigit():
        errs.append(f"mins must be a number, got {s.get('mins')!r}")
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
.mark{display:inline-flex;align-items:center;gap:.7rem;min-height:44px;font-weight:300;font-size:17px;
letter-spacing:.30em;text-transform:lowercase;text-decoration:none;color:var(--cream)}
.mark img{width:28px;height:28px;border-radius:50%}
.bar nav{display:flex;align-items:center;gap:1.4rem;font-size:.875rem;color:var(--dim)}
.bar nav a{text-decoration:none}
.bar nav a:hover{color:var(--text)}
.navbtn{border:1.5px solid var(--cream);color:var(--cream);border-radius:11px;padding:.55rem 1rem;
transition:background .18s ease}
.navbtn:hover{background:rgba(236,228,211,.10);color:var(--cream)}
@media(max-width:560px){.bar nav a:first-child{display:none}}
h1{font-family:var(--serif);font-weight:400;font-size:clamp(2rem,4.5vw,2.7rem);line-height:1.18;letter-spacing:-.015em;margin:0 0 1rem}
h2{font-family:var(--serif);font-weight:400;font-size:1.4rem;margin:2.5rem 0 1rem}
h3{font-family:var(--serif);font-weight:400;font-size:1.15rem;margin:2rem 0 .75rem}
.post-head{text-align:center;padding:2.5rem 0 2rem;max-width:42rem;margin-inline:auto}
.eyebrow{font:500 .75rem/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--iris-dim);margin-bottom:1.25rem}
.post-meta{font-size:.82rem;color:var(--dimmer)}
.post-meta b{color:var(--dim);font-weight:400}
.meta{font:500 .75rem/1.5 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--iris-dim);margin-bottom:2.5rem}
article p{font-family:var(--serif);font-size:1.08rem;line-height:1.75;color:var(--dim);margin-bottom:1.3rem}
article strong{color:var(--text);font-weight:400;font-style:italic}
article a{color:var(--text)}
article ul{margin:0 0 1.3rem 1.2rem;color:var(--dim);font-family:var(--serif);font-size:1.08rem;line-height:1.75}
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
font-size:1rem;font-weight:500;transition:background .18s ease}
.cta a:hover{background:#F5F0E6}
/* related content as cards; stories carry the app's gradient covers */
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

def post_cta():
    href, label = app_cta()
    return ('<div class="cta">\n'
            "<p>Lullable reads material like this aloud — warmly, slowly, and quieter "
            "every minute —\nuntil you drift off somewhere around the fourth clause.</p>\n"
            f'<a href="{href}">{label}</a>\n</div>')

def story_cta(s):
    href, label = app_cta()
    return (f'<div class="cta">\n<p>{html.escape(s["title"])} is {s["mins"]} minutes long, '
            f'read by {html.escape(s["narrator"])}, and ends quieter than it begins. '
            f'It lives in the Lullable app.</p>\n'
            f'<a href="{href}">{label}</a>\n</div>')

def page(title, desc, canonical, body, extra_head=""):
    nav_href, nav_label = app_cta()
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="en_US">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:image" content="{SITE}/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="{BRAND} — The Sleep Library" href="{SITE}/rss.xml">
<link rel="icon" href="/assets/brand/web/favicon.svg" type="image/svg+xml">
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
<a class="mark" href="/"><img src="/assets/brand/mark-128.webp" width="28" height="28" alt="" loading="lazy" decoding="async">{BRAND.lower()}</a>
<nav><a href="/stories/">Stories</a><a href="/sleep/">The Sleep Library</a><a class="navbtn" href="{nav_href}">{nav_label}</a></nav>
</header>
{body}
<footer>{BRAND} — the low-arousal knowledge engine. Not a medical device.
· <a href="/">Home</a> · <a href="/manifesto/">Manifesto</a> · <a href="/sleep/">The Sleep Library</a> · <a href="/stories/">Stories</a> · <a href="/#signup">Newsletter</a>
<br><a href="https://www.instagram.com/getlullable/" rel="me noopener" target="_blank">Instagram</a> · <a href="https://www.youtube.com/@getlullable" rel="me noopener" target="_blank">YouTube</a>
<br>© {date.today().year} Tecnologías Stellar, S.A. de C.V. · developed by <a href="https://stellartech.xyz" rel="noopener" target="_blank">stellartech.xyz</a> · <a href="/support/">Support</a> · <a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a> · <a href="#" data-consent>Cookie settings</a></footer>
</div>
<script src="/consent.js" defer></script>
</body>
</html>"""

def jsonld(schemas):
    # <-escape so no copy can break out of the script tag (SIMPLE.MX convention)
    return "".join('<script type="application/ld+json">'
                   + json.dumps(s).replace("<", "\\u003c")
                   + "</script>\n" for s in schemas)

def pretty(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%B %-d, %Y")

def related_html(items):
    # items: list of (url, title, kind, cover) — cover is ready-made markup for
    # stories, "" for essays. Only ever built from files on disk.
    if not items:
        return ""
    cards = "".join(
        f'<a class="rel" href="{u}">' + (cov or "")
        + f'<span class="kind">{k}</span><span class="t">{html.escape(t)}</span></a>'
        for u, t, k, cov in items)
    return f'<div class="related">\n<h2>Keep drifting</h2>\n<div class="rel-grid">{cards}</div>\n</div>'

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

def story_card(s, outdir):
    """Per-story share image via make-card.py. Optional: a missing card must
    never block a publish. If this python lacks Pillow, retry with the macOS
    system python (/usr/bin/python3), which ships with it here — homebrew's
    python3 took over PATH on 2026-08-11 and silently dropped the cards."""
    args = (str(outdir / "og.png"), s["title"],
            f"“{s['sample'].strip()}”",
            f"{s['mins']} minutes · read by {s['narrator']}",
            f"Last night, you drifted off during {s['title']}.")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("makecard", ROOT / "make-card.py")
        mc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mc)
        mc.card(*args[:4], headline=args[4])
        return True
    except Exception:
        import subprocess
        r = subprocess.run(["/usr/bin/python3", str(ROOT / "make-card.py"), *args],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return True
        print(f"  note: no share card for {s['slug']} ({r.stderr.strip()[:80] or 'no Pillow found'})")
        return False

# ---------------------------------------------------------------- build

def build():
    warnings = []
    posts = sorted((parse(p) for p in sorted((ROOT / "posts").glob("*.md"))),
                   key=lambda p: p["date"], reverse=True)
    stories = sorted((parse_story(p) for p in sorted((ROOT / "catalog").glob("*.md"))),
                     key=lambda s: s.get("date", ""), reverse=True)

    # gate first, write nothing on failure
    failures = []
    for p in posts:
        for e in validate_post(p, warnings):
            failures.append(f"{p['path']}: {e}")
    for s in stories:
        for e in validate_story(s, warnings):
            failures.append(f"{s['path']}: {e}")
    if failures:
        print("BUILD ABORTED — fix these before anything is written:")
        for f in failures: print("  HARD FAIL", f)
        sys.exit(1)
    for w in warnings:
        print("  warn:", w)

    (ROOT / "sleep").mkdir(exist_ok=True)
    (ROOT / "stories").mkdir(exist_ok=True)   # generated pages; sources live in catalog/

    # ---- posts
    for p in posts:
        url = f"{SITE}/sleep/{p['slug']}/"
        schemas = [{
            "@context": "https://schema.org", "@type": "Article",
            "headline": p["title"], "description": p["description"],
            "datePublished": p["date"], "mainEntityOfPage": url,
            "author": {"@type": "Organization", "name": BRAND, "url": SITE},
        }]
        if p.get("question"):
            schemas.append({
                "@context": "https://schema.org", "@type": "FAQPage",
                "mainEntity": [{"@type": "Question", "name": p["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": first_paragraph(p["body"])}}]})
        rel = [(f"/sleep/{o['slug']}/", o["title"], "essay", "") for o in posts if o["slug"] != p["slug"]][:2]
        rel += [(f"/stories/{s['slug']}/", s["title"], f"story · {s['mins']} min", story_cover(s))
                for s in stories[:2]]
        rendered = md(p["body"])
        # question posts: the first paragraph becomes "the short answer" card —
        # the block skimmers read and AI assistants quote
        if p.get("question"):
            rendered = re.sub(
                r"^<p>(.*?)</p>", lambda m:
                f'<div class="answer"><div class="lbl">The short answer</div><p>{m.group(1)}</p></div>',
                rendered, count=1, flags=re.S)
        kind = {"question": "A question, answered", "definition": "A definition",
                "fact-world": "A quiet fact-world"}.get(p.get("type", ""), "Essay")
        head_band = (f'<div class="post-head"><p class="eyebrow">The Sleep Library · {kind}</p>'
                     f"<h1>{html.escape(p['title'])}</h1>"
                     f'<p class="post-meta"><time datetime="{p["date"]}">{pretty(p["date"])}</time>'
                     f" · <b>{read_minutes(p['body'])} min read</b></p></div>")
        body = (f"<article>\n{head_band}\n<div class=\"measure\">\n{rendered}\n{post_cta()}\n</div>"
                f"\n{related_html(rel)}\n</article>")
        out = ROOT / "sleep" / p["slug"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(page(f"{p['title']} — {BRAND}", p["description"], url, body, jsonld(schemas)))

    # ---- blog index: card grid
    kinds = {"question": "Question", "definition": "Definition", "fact-world": "Fact-world"}
    items = "".join(
        f'<li class="idx-card"><div class="row">'
        f'<span class="chip">{kinds.get(p.get("type",""), "Essay")}</span>'
        f'<time datetime="{p["date"]}">{pretty(p["date"])} · {read_minutes(p["body"])} min</time></div>'
        f'<a href="/sleep/{p["slug"]}/">{html.escape(p["title"])}</a>'
        f'<p>{html.escape(p["description"])}</p></li>' for p in posts)
    body = (f'<div class="idx-head"><p class="eyebrow">The Sleep Library</p>'
            f"<h1>Quiet, true things to read at night.</h1>"
            f'<p class="post-meta">A new one most days. Nothing urgent, ever.</p></div>'
            f'<ul class="idx-grid">{items}</ul>')
    (ROOT / "sleep" / "index.html").write_text(
        page(f"The Sleep Library — {BRAND}", "Quiet, true essays on sleep, racing minds, and pleasantly "
             "uneventful knowledge. From Lullable, the low-arousal knowledge engine.", f"{SITE}/sleep/", body))

    # ---- story pages (the per-upload landing pages)
    for s in stories:
        url = f"{SITE}/stories/{s['slug']}/"
        out = ROOT / "stories" / s["slug"]
        out.mkdir(exist_ok=True)
        has_card = story_card(s, out)
        og = f"{SITE}/stories/{s['slug']}/og.png" if has_card else f"{SITE}/og.png"
        schemas = [{
            "@context": "https://schema.org", "@type": "AudioObject",
            "name": s["title"], "description": s["blurb"],
            "duration": f"PT{s['mins']}M", "inLanguage": "en",
            "isAccessibleForFree": s.get("premium", "true") == "false",
            "author": {"@type": "Organization", "name": BRAND, "url": SITE},
        }, {
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Stories", "item": f"{SITE}/stories/"},
                {"@type": "ListItem", "position": 2, "name": s["title"], "item": url}]}]
        head = jsonld(schemas) + f'<meta property="og:image" content="{og}">\n'
        chips = (f'<div class="chips"><span class="chip amber">▶ {s["mins"]} min</span>'
                 f'<span class="chip">{html.escape(s["genre"])}</span>'
                 f'<span class="chip">{html.escape(s["mood"])}</span>'
                 f'<span class="chip">read by {html.escape(s["narrator"])}</span>'
                 + ('' if s.get("premium") == "false" else '<span class="chip">Premium</span>')
                 + '</div>')
        siblings = [(f"/stories/{o['slug']}/", o["title"], f"{o['mins']} min · {o['genre']}", story_cover(o))
                    for o in stories if o["slug"] != s["slug"]][:3]
        essays = [(f"/sleep/{p['slug']}/", p["title"], "essay", "") for p in posts[:2]]
        sample = (f'<blockquote>“{html.escape(s["sample"].strip())}”</blockquote>'
                  f'<p class="meta" style="margin-top:-.5rem">The kind of sentence people fall asleep during</p>')
        head_band = (f'<div class="post-head"><div class="hero-cover">{story_cover(s, "200px")}</div>'
                     f'<p class="eyebrow">A Lullable sleep story</p>'
                     f"<h1>{html.escape(s['title'])}</h1>{chips}</div>")
        body = (f"<article>\n{head_band}\n<div class=\"measure\">\n"
                f"{md(s['body'])}\n{sample}\n{story_cta(s)}\n</div>\n{related_html(siblings + essays)}\n</article>")
        title = f"{s['title']} — a {s['mins']}-minute sleep story"
        (out / "index.html").write_text(page(f"{title} — {BRAND}", s["blurb"], url, body, head))

    # ---- stories index: card grid with gradient covers
    items = "".join(
        f'<li class="idx-card">{story_cover(s, "104px")}'
        f'<div class="row"><span class="chip amber">▶ {s["mins"]} min</span>'
        f'<span class="sub">{html.escape(s["genre"])} · {html.escape(s["narrator"])}</span></div>'
        f'<a href="/stories/{s["slug"]}/">{html.escape(s["title"])}</a>'
        f'<p>{html.escape(s["blurb"])}</p></li>' for s in stories)
    body = (f'<div class="idx-head"><p class="eyebrow">Stories</p>'
            f"<h1>Every story in the app.</h1>"
            f'<p class="post-meta">Endings given away, nothing withheld.</p></div>'
            f'<ul class="idx-grid">{items}</ul>')
    (ROOT / "stories" / "index.html").write_text(
        page(f"Sleep stories — {BRAND}", "Every sleep story in the Lullable app: slow fiction, nature and "
             "weather, folklore — read warmly and quieter every minute.", f"{SITE}/stories/", body))

    # ---- standing pages (/privacy/, /terms/, /support/) — same claim gate as
    # the essays, since "not a medical device" is the one sentence we cannot
    # get wrong. Anything dropped in legal/*.md becomes /<filename>/.
    legal = [parse_story(p) for p in sorted((ROOT / "legal").glob("*.md"))]
    for l in legal:
        hits = prohibited_claims_in(l["body"])
        if hits:
            sys.exit(f"HARD FAIL {l['path']}: prohibited claim(s) {hits}")
        url = f"{SITE}/{l['slug']}/"
        out = ROOT / l["slug"]
        out.mkdir(exist_ok=True)
        head_band = (f'<div class="post-head"><p class="eyebrow">{BRAND}</p>'
                     f"<h1>{html.escape(l['title'])}</h1>"
                     f'<p class="post-meta">Last updated <time datetime="{l["updated"]}">'
                     f'{pretty(l["updated"])}</time></p></div>')
        body = f'<article>\n{head_band}\n<div class="measure">\n{md(l["body"])}\n</div>\n</article>'
        (out / "index.html").write_text(page(f"{l['title']} — {BRAND}", l["description"], url, body))

    # ---- sitemap / rss / robots / llms
    urls = ([f"{SITE}/", f"{SITE}/manifesto/", f"{SITE}/sleep/", f"{SITE}/stories/"]
            + [f"{SITE}/{l['slug']}/" for l in legal]
            + [f"{SITE}/sleep/{p['slug']}/" for p in posts]
            + [f"{SITE}/stories/{s['slug']}/" for s in stories])
    sm = "\n".join(f"<url><loc>{u}</loc></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}\n</urlset>')

    rss_items = "".join(
        f"<item><title>{html.escape(p['title'])}</title>"
        f"<link>{SITE}/sleep/{p['slug']}/</link><guid>{SITE}/sleep/{p['slug']}/</guid>"
        f"<pubDate>{datetime.strptime(p['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc).strftime('%a, %d %b %Y 21:00:00 GMT')}</pubDate>"
        f"<description>{html.escape(p['description'])}</description></item>" for p in posts)
    (ROOT / "rss.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
        f"<title>{BRAND} — The Sleep Library</title><link>{SITE}/sleep/</link>"
        f"<description>Quiet, true things to read at night.</description>{rss_items}</channel></rss>")

    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")

    post_lines = "\n".join(f"- [{p['title']}]({SITE}/sleep/{p['slug']}/): {p['description']}" for p in posts)
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
        f"- [Stories]({SITE}/stories/): every sleep story in the app\n\n"
        f"## Essays\n{post_lines}\n\n## Stories\n{story_lines}\n\n"
        f"## Elsewhere\n"
        f"- [Instagram](https://www.instagram.com/getlullable/): the nightly fact cards\n"
        f"- [YouTube](https://www.youtube.com/@getlullable): full-length sleep stories to listen to\n\n"
        f"## About\n- Published by Tecnolog\u00edas Stellar, S.A. de C.V. (Mexico City), "
        f"built by stellartech.xyz. Contact: info@getlullable.com\n")

    print(f"built {len(posts)} posts + {len(stories)} story pages -> sleep/ stories/ "
          f"+ sitemap + rss + robots + llms.txt")

# ---------------------------------------------------------------- scaffolds

def scaffold_post(slug, topic=None):
    slug = re.sub(r"[^a-z0-9-]", "", slug.lower().replace(" ", "-"))
    path = ROOT / "posts" / f"{date.today().isoformat()}-{slug}.md"
    if path.exists():
        sys.exit(f"{path.name} already exists")
    t = topic or {}
    q = f"question: {t.get('title', 'Optional — the search question this answers. Delete if none.')}\n" \
        if (t.get("type") == "question" or not topic) else ""
    path.write_text(f"""---
title: {t.get('title', 'TITLE')}
description: Meta description under 155 characters.
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
    pending = [t for t in data["topics"] if t["slug"] not in published]
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
    return (url, "Get the app") if url else ("/#signup", "Join the waitlist")


APPLE_ID = "6800138113"   # App Store Connect record "GetLullable", confirmed 2026-08-12
STORE_URL = f"https://apps.apple.com/app/id{APPLE_ID}"


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
    HANDWRITTEN = [index, ROOT / "manifesto" / "index.html"]

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
    out, n_links = re.subn(
        r'(?P<tag><a\b[^>]*class="[^"]*app-link[^"]*"[^>]*)>(?P<body>.*?)</a>',
        link, out, flags=re.S)

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
