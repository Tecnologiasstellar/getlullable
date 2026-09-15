# Build-in-public posts — the creator program

Three posts about [/creators/](https://getlullable.com/creators/), written 2026-09-15,
each 1,300–1,330 characters so they paste into X (long post) or LinkedIn as they are.
One idea per post; they do not repeat each other's argument.

Suggested order: **1** first, **2** a few days later, **3** on or just after launch day,
when the two Apple facts in it are freshest. None of them states the price or makes any
claim about what the app does for sleep — keep it that way when editing.

Not in `posts/`, deliberately: `build.py` would publish anything there as an essay.

---

## 1. The honest number (founder-shaped)

People expect a $1 or $2 bounty per app download. Lullable's creator page says $0.50. Here is the arithmetic.

Lullable is an iPhone sleep-story app with a free tier and a paid one. Of the people who download it, maybe 2-3% go paid. Apple takes 15%. Half of those who pay leave after the first month. Run that through a year and a first-time download is worth roughly $0.30 to $0.65 to the business.

At $1-2 per download I lose money on every creator who does well. The usual move is to pay it anyway, call it growth, and quietly cut the rate later. I would rather say the real number now and explain it on the page, so the creators who join know what the deal is and why.

The rest of the terms follow the same logic. $0.50 per first-time download that Apple attributes to the creator's link. Pilot of 20 creators, capped at 500 paid downloads each per month. Monthly statement, paid 30 days later, $25 minimum, PayPal or Wise. Apple's campaign report is the ledger both sides see.

No per-signup bounty, because fake leads are cheap and fake downloads are not. No dashboard, no click counter, no affiliate platform. One link per creator (getlullable.com/go/theircode), a redirect rule, and Apple's numbers.

Creators say on air that they are paid. That is the law, and it is also the point.

getlullable.com/creators

---

## 2. The trick (engineering-shaped)

Here is the trick, in case it saves someone a week.

Lullable's affiliate program has no SDK, no vendor, no database. The entire attribution system is one redirect rule in vercel.json.

A creator gets one link: getlullable.com/go/theircode. Short enough to say on a podcast. Today it forwards to the homepage with ?ref=code, which the waitlist form already saves. On launch day the same rule sends iPhones to the App Store with the code as Apple's campaign token (ct=), and App Store Connect reports first-time downloads per code. Apple's report is the ledger, and both sides read the same one.

Cost: $0. No cookie, so no consent banner: the code lives in the URL and is stored only if someone joins the newsletter.

Two gotchas I did not know going in. Apple credits a download only within 24 hours of the tap, so the launch email has to carry each person's creator code or every pre-launch click is lost. And Apple's provider token (pt=) only exists after about a day of live downloads, so the campaign flip is a day-2 job, not day-0.

Pay is $0.50 per first-time download Apple attributes to the link. People expect $1-2; the page shows the arithmetic for why not.

Not built: dashboard, click counter, signup form, per-signup bounties. Two markdown files, about 40 lines of Python, one evening.

getlullable.com/creators

---

## 3. Two things I did not know (launch-day-shaped)

Two things I did not know yesterday morning, learned while building a creator program for an app that is not in the App Store yet.

One: Apple only credits a download to a campaign link if it happens within 24 hours of the tap. Not thirty days. Twenty-four hours. Every click a creator sends before launch day is worth nothing to them unless the same person comes back through a link on launch day.

Two: the provider token Apple needs in that link only exists after the app has about a day of live downloads. So the campaign link cannot be ready on day 0. It is a day-2 job.

The program shipped anyway, designed around both facts.

Each creator gets one link: getlullable.com/go/theircode. Today it is a redirect rule that sends people to the homepage with ?ref=code, and the waitlist form already saves that field, so the code rides along with the email. On launch day the same rule points iPhones at the App Store with the code as Apple's campaign token, and the launch email carries each person's creator code, so the click happens inside the 24-hour window. App Store Connect's report is the ledger both sides see.

No SDK, no database, no affiliate platform. Pay is $0.50 per first-time download Apple attributes to the link; the page shows the math. Creators say on air that they are paid.

getlullable.com/creators
