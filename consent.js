/* Cookie consent — one file, no vendor, no monthly bill.
   The promise in /privacy/ is that nothing optional loads until the visitor
   says yes. This is the code that keeps it. Rules, in order:
     1. Global Privacy Control set  -> declined, silently, no banner shown.
     2. A stored answer             -> honoured, no banner shown.
     3. Otherwise                   -> ask, and load nothing meanwhile.
   Paste the GA4 / Meta / TikTok snippets inside loadTags() and nowhere else.
   Anything pasted into a page's <head> defeats the whole thing. */
(function () {
  var KEY = "lull_consent";

  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }

  /* ---- the only place a tag may be loaded ---- */
  var loaded = false;
  function loadTags() {
    if (loaded) return;
    loaded = true;
    /* TODO paste here, in this order of appetite:
         - Google Analytics 4      (gtag.js)
         - Google Ads conversion   (same gtag)
         - Meta Pixel
         - TikTok Pixel
       Cookieless analytics needs no consent and may load in the page head.
       Google Consent Mode v2 is required for Google tags in the EEA — if you
       add it, default every signal to "denied" and call gtag('consent','update')
       from here, not from the head. */
  }

  function decline() {
    set("no");
    /* Nothing was loaded, so nothing needs unloading — but a visitor who says
       yes and then no gets a clean slate rather than a promise. */
    document.cookie.split(";").forEach(function (c) {
      var n = c.split("=")[0].trim();
      if (/^(_ga|_gid|_gcl|_fbp|_fbc|_tt|_ttp)/.test(n)) {
        document.cookie = n + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
        document.cookie = n + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=." + location.hostname;
      }
    });
  }

  var STYLE =
    "#lull-consent{position:fixed;right:1rem;left:auto;bottom:max(1rem,env(safe-area-inset-bottom));z-index:9999;width:calc(100% - 2rem);max-width:25rem;" +
    "background:#232532;border:1px solid rgba(233,233,237,.14);border-radius:14px;padding:1.05rem 1.15rem;" +
    "box-shadow:0 18px 44px rgba(0,0,0,.6);color:#B2B6CA;font:400 .84rem/1.55 Inter,ui-sans-serif," +
    "-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Roboto,sans-serif}" +
    "#lull-consent a{color:#ECE4D3}" +
    "#lull-consent .row{display:flex;gap:.6rem;margin-top:.9rem}" +
    "#lull-consent button{flex:1;min-height:44px;border-radius:10px;padding:.6rem .9rem;font:inherit;cursor:pointer}" +
    "#lull-consent .yes{background:transparent;border:1.5px solid #ECE4D3;color:#ECE4D3;font-weight:500}" +
    "#lull-consent .no{background:transparent;border:1.5px solid rgba(233,233,237,.14);color:#B2B6CA;font-weight:500}" +
    "#lull-consent .yes:hover{background:rgba(236,228,211,.10)}"+
    "#lull-consent .no:hover{color:#ECE4D3;border-color:rgba(233,233,237,.3)}";

  function banner() {
    if (document.getElementById("lull-consent")) return;
    var s = document.createElement("style"); s.textContent = STYLE;
    var d = document.createElement("div");
    d.id = "lull-consent";
    d.setAttribute("role", "dialog");
    d.setAttribute("aria-label", "Cookie choices");
    d.innerHTML =
      "Analytics and advertising cookies help us learn which page brought you here. " +
      "Decline and you still get the whole site — every essay, every story, the sample. " +
      '<a href="/privacy/">What we collect</a>.' +
      '<div class="row"><button class="yes">Accept</button><button class="no">Decline</button></div>';
    document.head.appendChild(s);
    document.body.appendChild(d);
    d.querySelector(".yes").onclick = function () { set("yes"); d.remove(); loadTags(); };
    d.querySelector(".no").onclick  = function () { decline(); d.remove(); };
  }

  /* footer "Cookie settings" links re-open the choice */
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-consent]");
    if (a) { e.preventDefault(); banner(); }
  });

  if (navigator.globalPrivacyControl === true) { set("no"); return; }
  var answer = get();
  if (answer === "yes") loadTags();
  /* Nothing optional loads before an answer either way, so the ask can wait a
     beat and let the page land first. It is a corner panel, not a wall: the
     visitor is never blocked, and no tag fires while it is on screen. */
  else if (answer !== "no") setTimeout(banner, 1200);
})();
