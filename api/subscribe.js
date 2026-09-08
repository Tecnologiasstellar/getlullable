/* POST {email, source} → Sender.net.
   Lives server-side because SENDER_API_TOKEN can read the whole list; it must
   never reach the browser. Set SENDER_API_TOKEN and SENDER_GROUP_ID in Vercel
   → Settings → Environment Variables (all environments). */
module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ ok: false });

  const { email, source } = req.body || {};
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
  if (!r.ok && r.status !== 422) {
    console.error("sender", r.status, await r.text().catch(() => ""));
    return res.status(502).json({ ok: false, error: "upstream" });
  }
  return res.status(200).json({ ok: true });
};
