#!/usr/bin/env python3
"""
Renders a "last fact you heard" card — the share image from MARKETING.md 1.5.

    python3 make-card.py                     # regenerates og.png with the demo fact
    python3 make-card.py out.png "the thermal vents of the Mariana Trench" "…and so it rises instead as a shimmering—" "Last listened at 11:41pm  ·  23 minutes of the deep ocean"

Design rules that are not negotiable (see MARKETING.md §4):
  - the quote ends mid-word or mid-clause. the truncation IS the joke.
  - the timestamp is exact. "around midnight" reads like marketing; 11:41pm reads true.
  - the timestamp is when the LISTENING stopped, never "asleep by": the app records
    a last-listened position, not a sleep onset, and the card may not claim more.
  - the wordmark is small and low-contrast. loud branding kills the joke.
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
# "Nocturne" tokens — the iOS app's palette, so the share card, the site and the
# app are one product (lullable_ios .../design_handoff_onboarding_flow/README.md).
# Georgia stands in for Newsreader, which isn't installed locally — same genre.
INK, TEXT, DIM, DIMMER = "#161826", "#ECE4D3", "#B2B6CA", "#8E92A8"
AMBER, IRIS = "#9184D9", "#9184D9"
F = "/System/Library/Fonts/Supplemental/Georgia"
PAD = 90

def font(px, italic=False):
    return ImageFont.truetype(f"{F} Italic.ttf" if italic else f"{F}.ttf", px)

def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def glow(img):
    """atmosphere is iris, per the system: a slow violet dusk from the top.
    built small and scaled up, so it's smooth and cheap."""
    s = 48
    g = Image.new("L", (s, s), 0)
    px = g.load()
    for y in range(s):
        for x in range(s):
            dx, dy = (x - s / 2) / (s * 0.5), y / (s * 0.75)
            d = (dx * dx + dy * dy) ** 0.5
            px[x, y] = max(0, int(40 * (1 - min(d, 1)) ** 2))
    mask = g.resize((W, H), Image.BICUBIC)
    img.paste(Image.new("RGB", (W, H), IRIS), (0, 0), mask)

def card(path, when, quote, footer, headline=None):
    img = Image.new("RGB", (W, H), INK)
    glow(img)
    d = ImageDraw.Draw(img)

    # wordmark
    d.ellipse([PAD, 62, PAD + 11, 73], fill=AMBER)
    d.text((PAD + 24, 55), "Lullable", font=font(24), fill=DIM)

    # the line that does the work — the template IS the brand voice
    h = font(44)
    y = 140
    text = headline or f"Last night, you drifted off while learning about {when}."
    for line in wrap(d, text, h, W - PAD * 2)[:2]:
        d.text((PAD, y), line, font=h, fill=TEXT)
        y += 60

    # the fact, truncated
    q = font(30, italic=True)
    y += 40
    for line in wrap(d, quote, q, W - PAD * 2)[:6]:
        d.text((PAD, y), line, font=q, fill=DIM)
        y += 46

    # footer rule + caption
    d.line([PAD, H - 112, W - PAD, H - 112], fill="#2B2741")
    d.text((PAD, H - 88), footer, font=font(22), fill=DIMMER)
    small = font(22)
    d.text((W - PAD - d.textlength("getlullable.com", font=small), H - 88),
           "getlullable.com", font=small, fill=DIMMER)

    img.save(path)
    print(f"wrote {path}")

if __name__ == "__main__":
    a = sys.argv[1:]
    card(
        a[0] if a else "og.png",
        a[1] if len(a) > 1 else "the thermal vents of the Mariana Trench",
        a[2] if len(a) > 2 else
        "“…the vent fluid, at nearly three hundred and sixty-five degrees, "
        "cannot boil under the weight of eleven kilometres of seawater, "
        "and so it rises instead as a shimmering—”",
        a[3] if len(a) > 3 else "Last listened at 11:41pm  ·  23 minutes of the deep ocean",
        headline=a[4] if len(a) > 4 else None,
    )
