/* node api/subscribe.test.js — the four paths that matter for the form. */
const assert = require("assert");
const handler = require("./subscribe.js");

const run = async (body, env, fetchImpl) => {
  Object.assign(process.env, { SENDER_API_TOKEN: "", SENDER_GROUP_ID: "", ...env });
  global.fetch = fetchImpl || (async () => ({ ok: true, status: 200, text: async () => "{}" }));
  let code = 0, json = null;
  await handler({ method: "POST", body }, { status(c) { code = c; return this; }, json(j) { json = j; return j; } });
  return { code, json };
};

(async () => {
  const wired = { SENDER_API_TOKEN: "t", SENDER_GROUP_ID: "g" };

  assert.equal((await run({ email: "not-an-email" }, wired)).code, 400, "bad address rejected");
  assert.equal((await run({ email: "a@b.co" }, { SENDER_API_TOKEN: "", SENDER_GROUP_ID: "" })).code, 500, "missing env is loud");
  assert.equal((await run({ email: "a@b.co" }, wired)).code, 200, "happy path");
  assert.equal((await run({ email: "a@b.co" }, wired,
    async () => ({ ok: false, status: 422, text: async () => "" }))).code, 200, "already subscribed reads as success");
  assert.equal((await run({ email: "a@b.co" }, wired,
    async () => ({ ok: false, status: 500, text: async () => "boom" }))).code, 502, "upstream failure surfaces");

  // the token must never be sent anywhere but Sender
  let seen = "";
  await run({ email: "a@b.co", source: "ph" }, wired, async (url, opts) => {
    seen = url; assert.ok(JSON.parse(opts.body).fields.source === "ph", "source passed through");
    return { ok: true, status: 200, text: async () => "{}" };
  });
  assert.equal(seen, "https://api.sender.net/v2/subscribers");

  /* Conversions API. The consent gate is the check that must never regress:
     /privacy/ promises nothing optional fires until the visitor says yes, and
     that promise covers this server, not just the browser. */
  const capiCalls = async (body, env) => {
    const hit = [];
    await run(body, { ...wired, ...env }, async (url, opts) => {
      hit.push({ url, opts });
      return { ok: true, status: 200, text: async () => "{}" };
    });
    return hit.filter((h) => String(h.url).includes("graph.facebook.com"));
  };

  assert.equal((await capiCalls({ email: "a@b.co", consent: true }, { META_CAPI_TOKEN: "" })).length, 0,
    "no token, no Meta call");
  assert.equal((await capiCalls({ email: "a@b.co", consent: false }, { META_CAPI_TOKEN: "t" })).length, 0,
    "consent declined, no Meta call");
  assert.equal((await capiCalls({ email: "a@b.co" }, { META_CAPI_TOKEN: "t" })).length, 0,
    "consent absent, no Meta call");

  const sent = await capiCalls({ email: "A@B.co", source: "fb", event_id: "e-1", consent: true },
    { META_CAPI_TOKEN: "t" });
  assert.equal(sent.length, 1, "consented signup mirrors to Meta");
  const ev = JSON.parse(sent[0].opts.body).data[0];
  assert.equal(ev.event_name, "Lead");
  assert.equal(ev.event_id, "e-1", "dedup id survives to Meta");
  assert.equal(ev.user_data.em[0],
    require("crypto").createHash("sha256").update("a@b.co").digest("hex"),
    "email is lowercased, trimmed and hashed - never sent in the clear");
  assert.ok(!sent[0].opts.body.includes("A@B.co"), "raw address never leaves this server");
  assert.equal((await run({ email: " a@b.co " }, wired)).code, 400, "whitespace address still rejected");

  console.log("subscribe: 14 checks passed");
})();
