#!/usr/bin/env python3
"""
The Sleep Library + Story pages — static generator. Zero runtime dependencies
(Pillow optional, for per-story share cards). Git is the CMS; disk is the queue.

    python3 build.py                 # validate + build everything
    python3 build.py next            # pick the next topic from topics.json (rotation
                                     #   rules applied) and scaffold its post
    python3 build.py new <slug>      # scaffold an off-queue post
    python3 build.py story <slug>    # scaffold a story page (new app upload)

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
:root{--ink:#0E0F16;--ink-2:#171823;--ink-3:#1F2130;--haze:#262937;--text:#EDE7DE;--dim:#9B97A8;
--dimmer:#6C6879;--amber:#DFAF83;--amber-soft:rgba(223,175,131,.28);--iris:#A79FD9;--iris-dim:#9C93CE;
--serif:Newsreader,Iowan Old Style,Palatino,Georgia,serif;
--sans:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif}
*{box-sizing:border-box;margin:0}
body{background:var(--ink);color:var(--text);font:400 17px/1.65 var(--sans);-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0 0 auto;height:50vh;pointer-events:none;
background:radial-gradient(110% 70% at 50% 0%,rgba(167,159,217,.07),transparent 62%)}
/* wide frame, centered reading measure — the measure protects the paragraphs,
   the frame gives everything else room to breathe */
.wrap{position:relative;max-width:56rem;margin:0 auto;padding:0 1.5rem}
.measure{max-width:36rem;margin-inline:auto}
header{padding:1.75rem 0}
.bar{display:flex;align-items:center;justify-content:space-between;gap:1rem}
.mark{display:inline-flex;align-items:center;gap:.6rem;font-family:var(--serif);font-size:1.15rem;text-decoration:none;color:var(--text)}
.dot{width:9px;height:9px;border-radius:50%;background:var(--amber);opacity:.85}
.bar nav{display:flex;align-items:center;gap:1.4rem;font-size:.875rem;color:var(--dim)}
.bar nav a{text-decoration:none}
.bar nav a:hover{color:var(--text)}
.navbtn{background:var(--amber);color:var(--ink);border-radius:8px;padding:.5rem .95rem;transition:opacity .3s}
.navbtn:hover{opacity:.85;color:var(--ink)}
@media(max-width:560px){.bar nav a:first-child{display:none}}
h1{font-family:var(--serif);font-weight:400;font-size:clamp(2rem,4.5vw,2.7rem);line-height:1.18;letter-spacing:-.015em;margin:0 0 1rem}
h2{font-family:var(--serif);font-weight:400;font-size:1.4rem;margin:2.5rem 0 1rem}
h3{font-family:var(--serif);font-weight:400;font-size:1.15rem;margin:2rem 0 .75rem}
.post-head{text-align:center;padding:2.5rem 0 2rem;max-width:42rem;margin-inline:auto}
.eyebrow{font:500 .72rem/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--iris-dim);margin-bottom:1.25rem}
.post-meta{font-size:.82rem;color:var(--dimmer)}
.post-meta b{color:var(--dim);font-weight:400}
.meta{font:500 .72rem/1.5 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--iris-dim);margin-bottom:2.5rem}
article p{font-family:var(--serif);font-size:1.08rem;line-height:1.75;color:var(--dim);margin-bottom:1.3rem}
article strong{color:var(--text);font-weight:400;font-style:italic}
article a{color:var(--text)}
article ul{margin:0 0 1.3rem 1.2rem;color:var(--dim);font-family:var(--serif);font-size:1.08rem;line-height:1.75}
article blockquote{border-left:2px solid var(--amber-soft);padding-left:1.25rem;margin:2rem 0;
font-family:var(--serif);font-style:italic;font-size:1.1rem;line-height:1.7;color:var(--dim)}
/* the short answer — the block AI assistants and skimmers both take */
.answer{background:linear-gradient(160deg,#1F1B2E,#131318);border:1px solid var(--haze);border-radius:16px;
padding:1.6rem 1.75rem;margin:0 0 2.5rem;box-shadow:0 12px 30px rgba(0,0,0,.5)}
.answer .lbl{font:500 .68rem/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--amber);margin-bottom:.8rem}
.answer p{margin:0;color:var(--text);font-size:1.12rem}
.chips{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:2rem;justify-content:center}
.chip{font:500 .72rem/1 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--iris-dim);
background:rgba(167,159,217,.12);border:1px solid rgba(167,159,217,.22);border-radius:20px;padding:.45rem .8rem}
.chip.amber{color:var(--amber);background:rgba(223,175,131,.12);border-color:rgba(223,175,131,.25)}
.cta{background:linear-gradient(160deg,#1F1B2E,#131318);border:1px solid var(--haze);border-radius:16px;
padding:1.75rem;margin:3.5rem 0;text-align:center;box-shadow:0 12px 30px rgba(0,0,0,.5)}
.cta p{font-family:var(--serif);color:var(--dim);margin-bottom:1.25rem}
.cta a{display:inline-block;background:var(--amber);color:var(--ink);border-radius:11px;
padding:.85rem 1.5rem;text-decoration:none;font-size:.95rem}
/* related content as cards; stories carry the app's gradient covers */
.related{border-top:1px solid var(--haze);margin-top:3.5rem;padding-top:2.5rem}
.related h2{margin-top:0;font-size:1.25rem;text-align:center;margin-bottom:1.75rem}
.rel-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1rem}
.rel{display:block;text-decoration:none;background:var(--ink-2);border:1px solid var(--haze);border-radius:14px;
padding:1.1rem;transition:border-color .3s}
.rel:hover{border-color:rgba(167,159,217,.35)}
.rel .cover{display:block;height:64px;border-radius:9px;margin-bottom:.8rem}
.g0{background:linear-gradient(150deg,#2B5064,#111D29)}.g1{background:linear-gradient(150deg,#2A2333,#191622)}
.g2{background:linear-gradient(150deg,#4C3760,#1B1628)}.g3{background:linear-gradient(150deg,#2B5148,#111F1C)}
.rel .kind{font:500 .62rem/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--dimmer);display:block;margin-bottom:.4rem}
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
.idx-card:hover{border-color:rgba(167,159,217,.35)}
.idx-card .row{display:flex;justify-content:space-between;align-items:center;margin-bottom:.9rem}
.idx-card time,.idx-card .sub{font-size:.75rem;color:var(--dimmer)}
.idx-card a{font-family:var(--serif);font-size:1.3rem;line-height:1.3;color:var(--text);text-decoration:none}
.idx-card a:hover{color:var(--iris)}
.idx-card p{color:var(--dim);font-size:.92rem;margin-top:.6rem;line-height:1.6}
@media(max-width:700px){.idx-grid{grid-template-columns:1fr}}
::selection{background:rgba(167,159,217,.3)}
"""

POST_CTA = """<div class="cta">
<p>Lullable reads material like this aloud — warmly, slowly, and quieter every minute —
until you drift off somewhere around the fourth clause.</p>
<a href="/#signup">Join the waitlist</a>
</div>"""

def story_cta(s):
    return (f'<div class="cta">\n<p>{html.escape(s["title"])} is {s["mins"]} minutes long, '
            f'read by {html.escape(s["narrator"])}, and ends quieter than it begins. '
            f'It lives in the Lullable app.</p>\n<a href="/#signup">Join the waitlist</a>\n</div>')

def page(title, desc, canonical, body, extra_head=""):
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
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:image" content="{SITE}/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="{BRAND} — The Sleep Library" href="{SITE}/rss.xml">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='9' fill='%23DFAF83'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;1,6..72,300&display=swap" rel="stylesheet">
{extra_head}<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="bar">
<a class="mark" href="/"><span class="dot"></span>{BRAND}</a>
<nav><a href="/stories/">Stories</a><a href="/sleep/">The Sleep Library</a><a class="navbtn" href="/#signup">Join the waitlist</a></nav>
</header>
{body}
<footer>{BRAND} — the low-arousal knowledge engine. Not a medical device.
· <a href="/">Home</a> · <a href="/manifesto/">Manifesto</a> · <a href="/sleep/">The Sleep Library</a> · <a href="/stories/">Stories</a> · <a href="/#signup">Newsletter</a></footer>
</div>
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
    # items: list of (url, title, kind, cover) — cover is a gradient class for
    # stories, "" for essays. Only ever built from files on disk.
    if not items:
        return ""
    cards = "".join(
        f'<a class="rel" href="{u}">'
        + (f'<span class="cover {cov}"></span>' if cov else "")
        + f'<span class="kind">{k}</span><span class="t">{html.escape(t)}</span></a>'
        for u, t, k, cov in items)
    return f'<div class="related">\n<h2>Keep drifting</h2>\n<div class="rel-grid">{cards}</div>\n</div>'

def cover_class(slug):
    return f"g{sum(ord(c) for c in slug) % 4}"

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
        rel += [(f"/stories/{s['slug']}/", s["title"], f"story · {s['mins']} min", cover_class(s["slug"]))
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
        body = (f"<article>\n{head_band}\n<div class=\"measure\">\n{rendered}\n{POST_CTA}\n</div>"
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
        siblings = [(f"/stories/{o['slug']}/", o["title"], f"{o['mins']} min · {o['genre']}", cover_class(o["slug"]))
                    for o in stories if o["slug"] != s["slug"]][:3]
        essays = [(f"/sleep/{p['slug']}/", p["title"], "essay", "") for p in posts[:2]]
        sample = (f'<blockquote>“{html.escape(s["sample"].strip())}”</blockquote>'
                  f'<p class="meta" style="margin-top:-.5rem">The kind of sentence people fall asleep during</p>')
        head_band = (f'<div class="post-head"><p class="eyebrow">A Lullable sleep story</p>'
                     f"<h1>{html.escape(s['title'])}</h1>{chips}</div>")
        body = (f"<article>\n{head_band}\n<div class=\"measure\">\n"
                f"{md(s['body'])}\n{sample}\n{story_cta(s)}\n</div>\n{related_html(siblings + essays)}\n</article>")
        title = f"{s['title']} — a {s['mins']}-minute sleep story"
        (out / "index.html").write_text(page(f"{title} — {BRAND}", s["blurb"], url, body, head))

    # ---- stories index: card grid with gradient covers
    items = "".join(
        f'<li class="idx-card"><span class="cover {cover_class(s["slug"])}" '
        f'style="display:block;height:76px;border-radius:10px;margin-bottom:1rem"></span>'
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

    # ---- sitemap / rss / robots / llms
    urls = ([f"{SITE}/", f"{SITE}/manifesto/", f"{SITE}/sleep/", f"{SITE}/stories/"]
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
        f"## Essays\n{post_lines}\n\n## Stories\n{story_lines}\n")

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

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "new" and len(args) > 1:
        scaffold_post(args[1])
    elif args and args[0] == "next":
        next_topic()
    elif args and args[0] == "story" and len(args) > 1:
        scaffold_story(args[1])
    else:
        build()
