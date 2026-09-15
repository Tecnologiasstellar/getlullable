# Creator program — the internal process

The public side is [/creators/](https://getlullable.com/creators/) and
[/creator-terms/](https://getlullable.com/creator-terms/). This is the private side: how a
creator gets in, how a download gets attributed, how money goes out, and what to do on
launch day. Visual version, same content: the "Lullable Creator Playbook" artifact,
https://claude.ai/artifact/SsjTpnUDEQ2rxr1jfuYLbM (private to AV's Claude account; share from the page if needed).

**The deal, fixed 2026-09-14:** US$0.50 per first-time download Apple attributes to the
creator's link · pilot of 20 creators · cap 500 paid downloads per creator per month ·
statement on the 1st · paid 30 days later · US$25 minimum, rolls forward · PayPal or Wise.
Downloads only. Never per signup, never per click.

## 1. Getting a creator in

1. They email `info@getlullable.com` (the page pre-fills: name, links, audience size,
   wanted code, payout rail). Reply within a week, always by a person.
2. Approve if: a real audience, bedtime-shaped (sleep, ADHD, history/science, slow
   content, parenting), and they can say the mechanism without promising a result.
   Decline coupon/deal sites, paid-search operators, anyone who needs a medical claim.
3. Pick the code with them: lowercase letters, numbers or hyphens, 2–30 characters,
   usually their show or handle. It must match `[a-z0-9-]{2,30}` or `/go/` 404s.
4. Add a row to the sheet: name · email · platform · handle · code · payout rail ·
   payout address · approved on · status (pilot slot 1–20).
5. Send the welcome email: their link `getlullable.com/go/<code>`, the page URL, the
   terms URL, the disclosure line, and — until Apple's tag exists — "hold your push until
   we email you that it counts."

Nothing is configured on the site per creator. Any slug that matches the regex works;
we pay only the codes in the sheet.

## 2. How a download is attributed

```
creator says the link ──► listener taps getlullable.com/go/<code>
                                     │  (307, no cookie, nothing stored)
        ┌────────────────────────────┴────────────────────────────┐
   TODAY (waitlist)                                        AFTER GOLIVE
   → /?ref=<code>                            iPhone → App Store listing with
   → signup form saves source=<code>            pt=<APPLE_PT>&ct=<code>&mt=8
     in Sender                                 others → /?ref=<code>
   → reported to the creator, not paid       → Apple counts a FIRST-TIME download
                                               if it happens within 24h of the tap
                                               (most recent link wins)
                                             → App Store Connect › Analytics ›
                                               Acquisition › Campaigns, per ct
                                             → the sheet → statement → payout
```

Where it lives: `build.py` writes the `/go/` rules into `vercel.json` from the launch
constant (`go_rules()`, `sync_go_rules()`); `APPLE_PT` holds Apple's provider token;
`launch_copy()` rewrites the creators-page paragraph to match. One constant, no second copy.

What Apple's report does and doesn't do:

- Counts **first-time downloads** per campaign token, full-population (no opt-in bias).
  Re-downloads are listed separately and are not paid.
- Shows a campaign only once it has **5** first-time downloads; each metric needs 5 in the
  selected range. A small creator's first month can legitimately read as zero.
- Lags **24–72 h**. Read it on the 1st for the previous calendar month, never on the 31st.
- Read the **dashboard**. The Analytics Reports API's detailed report is privacy-noised
  and runs ~40% low; it is not the ledger.
- Also shows product page views, proceeds and paying users per token — useful context,
  not what we pay on.

## 3. The monthly ritual (1st of the month, ~30 minutes)

1. App Store Connect › the app › Analytics › Acquisition › Campaigns › date range = last
   calendar month. Note **First-Time Downloads** per campaign name (= code).
2. Sheet, one row per creator per month: downloads · paid downloads = min(downloads, 500)
   · commission = paid × $0.50 · carried from last month · balance · paid? · date.
3. Email each creator their statement (downloads, commission, balance, when it pays).
   Creators under the 5-download threshold still get an email: "under Apple's threshold
   this month; nothing to report yet."
4. Pre-launch months: report waitlist signups per code instead — Sender › subscribers ›
   filter `source` = code. Reported, not paid.
5. 30 days later: pay every balance ≥ $25 (Wise Business batch or PayPal), mark paid.
6. Once a quarter: open one recent post/episode per active creator and check the
   disclosure is spoken or shown at the start. Missing disclosure = that month's
   downloads are withheld (terms §6) and a warning email.

## 4. Launch day, in order

1. `python3 build.py appstore` goes green → `python3 build.py golive` → `python3 build.py`
   → browser-verify → `python3 build.py ship "Launch: get the app"`. This flips every
   CTA, the `/go/` rules (iPhone → store) and the creators paragraph in one build.
2. **Day 2:** App Store Connect › Analytics › Acquisition › Campaigns › (+) shows the
   `pt=` provider token (it does not exist until ~24 h of live downloads). Paste it into
   `APPLE_PT` in `build.py`, build, ship. Verify:
   `curl -sI -A iPhone https://getlullable.com/go/testcode` → 307 to
   `apps.apple.com/app/apple-store/id6800138113?pt=…&ct=testcode&mt=8`.
3. **Only then** send the waitlist launch email, button URL
   `https://getlullable.com/go/{{ source | default: "waitlist" }}` (Sender Liquid;
   test-send once first). And email every creator: "your link is counting from today."
   Downloads before the token exists cannot be tied to a code — the page tells creators
   to hold, so we must not send the email early.

## 5. Rules we hold ourselves to

- Pay only what the App Store Connect dashboard shows. No estimates, no clicks, no signups.
- Never ask a creator to solicit reviews (App Store guideline 5.6.3); never pay end users
  to download (3.2.2). Paying a creator per referred download is fine.
- No attribution SDK in the app — the privacy policy promises it, and Apple's report makes
  it unnecessary.
- No dashboard, click counter, offer codes or signup form until a real creator asks and
  the ritual above hurts. If click counts are ever wanted on Vercel Hobby, redirect
  `/go/<code>` to a static path instead of `?ref=` so the Pages panel counts it.
- Refunds do not change download counts; nothing to claw back for refunds. Clawback is
  for fraud or a breach of the terms only.
- Vercel Hobby is contractually non-commercial; this program is the moment Pro ($20/mo)
  becomes the honest plan. AV's call.

## 6. Edge cases

| Situation | What happens | What to do |
|---|---|---|
| Creator types the code in capitals | Vercel matches the path case-insensitively; the token keeps the case typed | Issue lowercase codes; if a mixed-case campaign appears in Apple, add both rows for that creator |
| Listener downloads 2 days after the tap | Apple does not credit it | Nothing; the page and terms say so |
| Creator hits 500 in a month | Commission stops at 500 | Statement shows downloads and paid downloads separately; raise the cap deliberately, in writing |
| Creator asks for numbers mid-month | Dashboard is live minus 24–72 h | Send the current figure with the lag and the 5-threshold caveat |
| Code appears in Apple that we never issued | Someone shared a made-up slug | Not paid; nothing to do |
| `APPLE_PT` still empty a week after launch | Every download unattributed | Do step 4.2 today; email creators the date it started counting |
