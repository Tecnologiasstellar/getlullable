#!/usr/bin/env python3
"""
Schedules a month of Instagram cards on PostPeer. One sitting per month.

    python3 ig-schedule.py --dry-run     # print the plan, touch nothing
    python3 ig-schedule.py               # schedule this month's remaining slots
    python3 ig-schedule.py --month 2026-09

Why batch and not a daily cron: PRODUCTION.md's rule, learned twice — crons fail
silently. PostPeer's servers do the publishing, so nothing here has to be awake,
and there is exactly one thing to check each month instead of nineteen.

Disk is the queue, again: ig-posted.json is the record. A slug is consumed when
it appears there. Re-running is safe — already-scheduled slugs are skipped.
"""
import json, os, sys, urllib.error, urllib.request
from calendar import monthrange
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).parent
FACTS, POSTED = HERE / "ig-facts.json", HERE / "ig-posted.json"

API = "https://api.postpeer.dev/v1/posts"
ACCOUNT = "6a7e005ceabdac5f91c1e4bf"          # @getlullable, from /v1/connect/integrations
BASE = "https://getlullable.com/ig"
TZ = "America/Mexico_City"                    # AV's clock; 21:07 here is evening across the US
AT = "21:07"
CAP = 19                                      # PostPeer free tier. This number is the whole budget.
TAGS = "\n\n#sleep #rest #sleepbetter #bedtime #nightroutine"


def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def slots(year, month, n, after):
    """Weekday evenings, starting the day after `after`. Weekends are skipped so
    the feed has a working rhythm; the cap is what actually protects the tier.

    The offset is not optional. PostPeer rejects a bare "...T21:07:00" outright,
    and stores a trailing Z as literal UTC — which would post these at 3pm. The
    zone is resolved per date so a DST-observing TZ still lands at 21:07 local."""
    hh, mm = (int(x) for x in AT.split(":"))
    out = []
    for day in range(1, monthrange(year, month)[1] + 1):
        d = date(year, month, day)
        if d <= after or d.weekday() > 4:
            continue
        out.append(datetime.combine(d, time(hh, mm), ZoneInfo(TZ)).isoformat())
        if len(out) == n:
            break
    return out


def pick(facts, used, n):
    """A quote every fifth card, counted across the whole history — not per month.
    The bank runs about four facts to every quote, so alternating strictly would
    spend all the quotes in three weeks and leave the rest of the grid flat."""
    quotes = [f for f in facts if f.get("type") == "quote" and f["slug"] not in used]
    rest = [f for f in facts if f.get("type") != "quote" and f["slug"] not in used]
    queue = []
    for i in range(n):
        pool = quotes if (len(used) + i + 1) % 5 == 0 and quotes else rest
        pool = pool or rest or quotes
        if not pool:
            break
        queue.append(pool.pop(0))
    return queue


def live(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except urllib.error.URLError:
        return False


def schedule(fact, when, key):
    body = json.dumps({
        "content": fact["caption"] + TAGS,
        "mediaItems": [{"url": f"{BASE}/{fact['slug']}.png", "type": "image"}],
        "platforms": [{"platform": "instagram", "accountId": ACCOUNT}],
        "scheduledFor": when,
        "timezone": TZ,
    }).encode()
    req = urllib.request.Request(API, data=body, method="POST", headers={
        "x-access-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    if "--month" in args:
        year, month = (int(x) for x in args[args.index("--month") + 1].split("-"))
    else:
        year, month = date.today().year, date.today().month

    facts, posted = load(FACTS, []), load(POSTED, [])
    mine = [p for p in posted if p["scheduledFor"].startswith(f"{year}-{month:02d}")]
    room = CAP - len(mine)
    if room <= 0:
        print(f"{year}-{month:02d}: {len(mine)}/{CAP} already scheduled. Nothing to do.")
        return

    taken = {p["scheduledFor"] for p in mine}
    after = date.today() if (year, month) == (date.today().year, date.today().month) \
        else date(year, month, 1) - timedelta(days=1)
    when = [s for s in slots(year, month, room + len(taken), after) if s not in taken][:room]
    queue = pick(facts, {p["slug"] for p in posted}, len(when))

    if len(queue) < len(when):
        print(f"! bank has only {len(queue)} unused cards for {len(when)} slots — top up facts.json")
        when = when[:len(queue)]
    if not when:
        print("No slots left this month.")
        return

    print(f"{year}-{month:02d}: {len(mine)} scheduled, {len(when)} to add (cap {CAP})\n")
    for f, w in zip(queue, when):
        print(f"  {w[:10]} {AT}  {f['slug']}")

    missing = [f["slug"] for f in queue if not live(f"{BASE}/{f['slug']}.png")]
    if missing:
        print(f"\n! not live yet: {', '.join(missing)}")
        print("  push the repo first — PostPeer fetches these URLs at publish time.")
        return
    print("\nall images live.")
    if dry:
        return

    key = os.environ.get("POSTPEER_KEY")
    if not key:
        sys.exit("POSTPEER_KEY not set (source .env)")

    for f, w in zip(queue, when):
        try:
            res = schedule(f, w, key)
        except urllib.error.HTTPError as e:
            print(f"  FAILED {f['slug']}: {e.code} {e.read().decode()[:200]}")
            break
        posted.append({"slug": f["slug"], "scheduledFor": w,
                       "id": res.get("post", {}).get("id") or res.get("id"),
                       "at": datetime.now().isoformat(timespec="seconds")})
        POSTED.write_text(json.dumps(posted, indent=2) + "\n")
        print(f"  scheduled {f['slug']} for {w}")


if __name__ == "__main__":
    main()
