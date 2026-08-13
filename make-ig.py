#!/usr/bin/env python3
"""
Renders the daily Instagram card — 1080x1350, solid Nightfall ink, Newsreader.

    .venv/bin/python make-ig.py                        # render every unrendered card in ig-facts.json
    .venv/bin/python make-ig.py --slug second-sleep    # render one, overwriting
    .venv/bin/python make-ig.py --all                  # re-render everything (after a template change)

Design rules, from the live site's CSS vars and MARKETING.md 4:
  - solid background, one accent, nothing else. No photos, no people, no gradients.
  - type IS the design: Newsreader light on ink, generous margins, one idea per card.
  - the wordmark is small and low-contrast. Loud branding kills the credibility.
  - the size autofits so a 9-word quote and a 40-word fact both look deliberate.

Disk is the queue: a fact is consumed when ig/<slug>.png exists. Delete the png
to re-open it. Same rule as topics.json, no status fields anywhere.
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from build import prohibited_claims_in    # noqa: E402 — one gate, shared with the site

OUT = ROOT / "ig"
FACTS = ROOT / "ig-facts.json"

W, H = 1080, 1350                      # 4:5 — the tallest Instagram allows in-feed
PAD = 96
MEASURE = W - PAD * 2

# Nightfall tokens, copied from index.html. If these drift from the site, the
# site wins — it is what a visitor actually sees after they tap the link.
INK, TEXT, DIM, DIMMER = "#0E0F16", "#EDE7DE", "#9B97A8", "#6C6879"
AMBER, HAZE = "#DFAF83", "#262937"

ROMAN = ROOT / "fonts" / "Newsreader.ttf"
ITALIC = ROOT / "fonts" / "Newsreader-Italic.ttf"


def font(px, weight=300, italic=False):
    """Newsreader is a variable font: weight 200-800, optical size 6-72.
    Tracking opsz to the render size is what keeps small text from going spindly."""
    f = ImageFont.truetype(str(ITALIC if italic else ROMAN), px)
    f.set_variation_by_axes([weight, max(6, min(72, round(px * 0.6)))])
    return f


def smarten(s):
    """Straight quotes are a tell that a machine set the type. Newsreader has the
    real glyphs; the bank is written in plain ASCII and converted here, once."""
    out, open_d = [], True
    for ch in s:
        if ch == '"':
            out.append("“" if open_d else "”")
            open_d = not open_d
        elif ch == "'":
            out.append("’")          # always an apostrophe here; the bank has no single quotes
        else:
            out.append(ch)
    return "".join(out).replace(" - ", " — ")


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def autofit(draw, text, max_h, max_px=88, min_px=40):
    """Largest size where the block still fits the well. Long facts and short
    quotes then arrive at the same visual weight without per-card fiddling."""
    for px in range(max_px, min_px - 1, -2):
        f = font(px)
        lines = wrap(draw, text, f, MEASURE)
        if len(lines) * round(px * 1.34) <= max_h:
            return f, lines, round(px * 1.34)
    f = font(min_px)
    return f, wrap(draw, text, f, MEASURE), round(min_px * 1.34)


def card(path, text, attrib=None):
    text, attrib = smarten(text), smarten(attrib) if attrib else None
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)

    # wordmark, top left — the amber dot is the entire logo
    d.ellipse([PAD, 92, PAD + 13, 105], fill=AMBER)
    d.text((PAD + 28, 82), "Lullable", font=font(30, 400), fill=DIM)

    # the well the quote lives in: below the wordmark, above the footer rule
    TOP, BOT = 250, H - 210
    attrib_h = 76 if attrib else 0
    fnt, lines, lh = autofit(d, text, (BOT - TOP) - attrib_h - 60)

    block_h = len(lines) * lh + attrib_h
    y = TOP + ((BOT - TOP) - block_h) // 2

    # the one accent on the card
    d.rectangle([PAD, y - 54, PAD + 68, y - 51], fill=AMBER)

    for line in lines:
        d.text((PAD, y), line, font=fnt, fill=TEXT)
        y += lh

    if attrib:
        d.text((PAD, y + 30), attrib, font=font(32, 300, italic=True), fill=DIM)

    # footer
    d.line([PAD, H - 150, W - PAD, H - 150], fill=HAZE)
    d.text((PAD, H - 122), "getlullable.com", font=font(28, 400), fill=DIMMER)

    img.save(path)
    return path


def main():
    args = sys.argv[1:]
    facts = json.loads(FACTS.read_text())
    only = args[args.index("--slug") + 1] if "--slug" in args else None
    force = "--all" in args or only

    # The expensive failure, same gate build.py uses. A card is harder to retract
    # than a page: it's already in someone's feed. Abort the batch, don't skip one.
    hits = [(f["slug"], h) for f in facts
            if (h := prohibited_claims_in(f["text"] + " " + f.get("attrib", "") + " " + f["caption"]))]
    if hits:
        sys.exit("prohibited claim(s):\n" + "\n".join(f"  {s}: {', '.join(h)}" for s, h in hits))

    wrote = 0
    for f in facts:
        if only and f["slug"] != only:
            continue
        path = OUT / f"{f['slug']}.png"
        if path.exists() and not force:
            continue
        card(path, f["text"], f.get("attrib"))
        print(f"wrote ig/{f['slug']}.png")
        wrote += 1
    print(f"{wrote} card(s); {len(facts)} in the bank")


if __name__ == "__main__":
    main()
