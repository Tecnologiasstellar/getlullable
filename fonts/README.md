# Fonts

Self-hosted, on purpose. The site makes **no request to a third party** — the
browser never tells Google (or anyone) who is reading a sleep-stories site at
1am, and `/privacy/` can therefore say "we load nothing from anyone else" and
mean it. It is also the safer reading of GDPR: several EU decisions have treated
an IP address sent to Google Fonts as a transfer that needs consent, and the
cheapest way to never have that argument is to not make the request.

Decided 2026-08-25.

## What's here

| File | Family | Style | Weights | Bytes |
|---|---|---|---|---|
| `inter-latin.woff2` | Inter | normal | 300–600 (variable) | 48,432 |
| `newsreader-italic-latin.woff2` | Newsreader | italic | 300–500 (variable) | 64,500 |
| `newsreader-latin.woff2` | Newsreader | normal | 300–500 (variable) | 58,152 |

The homepage preloads Inter + Newsreader italic; the generated pages preload
Inter + Newsreader roman. Each is a variable font, so one file covers every
weight the site sets.

`Newsreader.ttf` and `Newsreader-Italic.ttf` are unrelated to the web pages —
they are the desktop files [make-ig.py](../make-ig.py) renders Instagram cards
with.

## Provenance

These are Google's own **latin-subset woff2 builds**, fetched once from
`fonts.gstatic.com` and committed. They are byte-identical to what the CDN was
serving; nothing was re-subset or re-compressed locally, so there is no
fontTools dependency and no build step.

The `@font-face` blocks (in `index.html` and in `build.py`'s `CSS`) carry
Google's own `unicode-range` for the latin subset. Two characters used on the
site fall outside it — `→` (U+2192) and any `▶` — and fall back to the system
face, exactly as they did before. Everything else, including `í` in *Tecnologías
Stellar*, is inside the range.

## Licence

Both families are under the **SIL Open Font License 1.1**, which explicitly
permits redistribution and self-hosting, including bundled with a website. No
attribution is required in the UI.

- Inter — Rasmus Andersson · <https://github.com/rsms/inter>
- Newsreader — Production Type · <https://github.com/productiontype/Newsreader>

## Re-fetching

If a family ever needs a new weight, get the CSS with a modern-browser
User-Agent (so Google returns woff2), take the `latin` block's URL, and replace
the file in place — the `@font-face` rules do not change:

```bash
curl -s -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36" "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap"
```

Do **not** add the `opsz` axis back to Newsreader: the variable latin subset
with optical sizing is 147 KB against 64 KB for the plain weight axis, and the
site only ever sets it at one size band.
