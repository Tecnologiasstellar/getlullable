/* POST {email, source, event_id, consent} → Sender.net, then Meta's Conversions
   API if the visitor consented.
   Lives server-side because SENDER_API_TOKEN can read the whole list; it must
   never reach the browser. Set SENDER_API_TOKEN and SENDER_GROUP_ID in Vercel
   → Settings → Environment Variables (all environments). */
module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ ok: false });

  const { email, source, event_id, consent } = req.body || {};
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email || "")) {
    return res.status(400).json({ ok: false, error: "unfinished" });
  }
  if (!process.env.SENDER_API_TOKEN || !process.env.SENDER_GROUP_ID) {
    console.error("subscribe: SENDER_API_TOKEN or SENDER_GROUP_ID missing");
    return res.status(500).json({ ok: false, error: "unwired" });
  }

  const r = await fetch("https://api.sender.net/v2/subscribers", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.SENDER_API_TOKEN}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      email,
      groups: [process.env.SENDER_GROUP_ID],
      trigger_automation: true,
      fields: { source: String(source || "web").slice(0, 40) },
    }),
  });

  /* An address already on the list comes back 422. That is a success for the
     person standing at the form, and telling them otherwise would confirm to a
     stranger whether an address is subscribed. */
  /* Log what Sender said either way. When a signup silently fails to produce
     an email, the answer is always in this line: the subscriber's status. */
  const said = await r.text().catch(() => "");
  console.log("sender", r.status, said.slice(0, 400));
  /* Already-on-the-list is a success for the person standing at the form, and
     Sender has more than one way of saying it (422, 409, or a 400 whose body
     mentions the address exists). Anything else is a real failure. */
  const dup = r.status === 409 || r.status === 422 || /already|exist|duplicate/i.test(said);
  if (!r.ok && !dup) {
    /* Print the address too: while Sender is refusing, this log line is the
       only record that someone tried to join, and they can be added by hand. */
    console.error("subscribe LOST", email, "sender said", r.status);
    return res.status(502).json({ ok: false, error: "upstream", status: r.status });
  }
  /* Meta Conversions API. Server-side twin of the browser's fbq("Lead"), sharing
     event_id so Meta keeps exactly one of them. It exists because the browser
     pixel is blocked for a large share of real people — ad blockers, iOS
     tracking prevention, a declined banner. This path still respects the
     banner: `consent` is what the visitor chose, and no consent means no call.
     Failure here must never cost us the subscriber, so it is caught and logged. */
  if (consent && process.env.META_CAPI_TOKEN) {
    try {
      await sendMetaLead({ email, source, event_id, req });
    } catch (e) {
      console.error("capi failed", e && e.message);
    }
  }

  return res.status(200).json({ ok: true });
};

const PIXEL_ID = "2120190601930707";

const sha256 = (v) =>
  require("crypto").createHash("sha256").update(String(v).trim().toLowerCase()).digest("hex");

/* Meta matches on hashed email plus whatever browser identifiers came along.
   _fbp and _fbc are ordinary cookies, so they arrive on this request already. */
async function sendMetaLead({ email, source, event_id, req }) {
  const cookies = String(req.headers?.cookie || "");
  const cookie = (n) => (cookies.match(new RegExp("(?:^|; )" + n + "=([^;]+)")) || [])[1];

  const r = await fetch(
    `https://graph.facebook.com/v21.0/${PIXEL_ID}/events?access_token=${process.env.META_CAPI_TOKEN}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        data: [
          {
            event_name: "Lead",
            event_time: Math.floor(Date.now() / 1000),
            event_id: event_id || undefined,
            event_source_url: "https://getlullable.com/",
            action_source: "website",
            custom_data: { content_name: "Sunday letter", source: String(source || "web") },
            user_data: {
              em: [sha256(email)],
              client_ip_address: String(req.headers?.["x-forwarded-for"] || "").split(",")[0].trim() || undefined,
              client_user_agent: req.headers?.["user-agent"] || undefined,
              fbp: cookie("_fbp"),
              fbc: cookie("_fbc"),
            },
          },
        ],
      }),
    }
  );
  /* Meta answers 200 with events_received, or 400 with a diagnostic worth
     reading. Either way it goes in the log and nowhere near the visitor. */
  console.log("capi", r.status, (await r.text().catch(() => "")).slice(0, 300));
}
