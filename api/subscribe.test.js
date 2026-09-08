/* node api/subscribe.test.js — the four paths that matter for the form. */
const assert = require("assert");
const handler = require("./subscribe.js");

const run = async (body, env, fetchImpl) => {
  Object.assign(process.env, { SENDER_API_TOKEN: "", SENDER_GROUP_ID: "", ...env });
  global.fetch = fetchImpl || (async () => ({ ok: true, status: 200 }));
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
    return { ok: true, status: 200 };
  });
  assert.equal(seen, "https://api.sender.net/v2/subscribers");

  console.log("subscribe: 6 checks passed");
})();
