#!/usr/bin/env node
/* Regression harness for the GA4 outbound-click partial.
 *
 * WHY THIS EXISTS
 * The partial (layouts/partials/extend_footer.html) fires a GA4
 * `outbound_click` event when a reader leaves for a product URL. It is silent
 * JavaScript, so a broken version looks exactly like a working one: no errors,
 * no console output, just no data ever appearing in GA4. That failure mode is
 * indistinguishable from "nobody clicked" — which is precisely the question the
 * tracking exists to answer. Hence a test that asserts the routing decisions.
 *
 * RUN:  node scripts/test_outbound_tracking.js
 *       (needs `hugo` to have built public/ first)
 *
 * WHAT IT ASSERTS
 *   1. App Store links fire (any locale path).
 *   2. The product page fires.
 *   3. Internal navigation does NOT fire — otherwise every pageview double-counts.
 *   4. Untracked external links do NOT fire.
 *   5. Relative links do NOT fire.
 *   6. link_domain is derived, not hardcoded — so future products are labelled
 *      correctly rather than all reporting apps.apple.com.
 *
 * ⚠️ Do not "simplify" by asserting only that the string `outbound_click`
 * appears in the built HTML. That passes even when the handler never runs,
 * which is the exact bug this file was written to catch.
 */
const fs = require("fs");

const path = require("path");

// ⚠️ 2026-11-26: this used to hardcode /tmp/tdreview/public/... — a scratch dir
// from one old review session. It existed for whoever wrote this and for nobody
// else, so the test failed locally forever while CI never ran it (the workflow
// does not invoke this script). Resolve against the real repo instead.
const BUILT =
  process.env.TRAINDECADE_BUILT ||
  path.resolve(__dirname, "..", "public", "posts", "whey-vs-beef-protein", "index.html");
if (!fs.existsSync(BUILT)) {
  console.error(`❌ ${BUILT} not found — run 'hugo' in the repo first.`);
  process.exit(1);
}

const html = fs.readFileSync(BUILT, "utf8");
// ⚠️ 2026-11-26 — this extraction was fragile three ways over:
//   1. literal space after `function` — `hugo --minify` emits `(function(){`
//   2. required trailing `;`           — minified output ends `})()` with no semicolon
//   3. matched the WRONG IIFE          — the page has several `(function(){` blocks;
//      a lazy match from the top grabbed the email-capture script, which calls
//      document.getElementById and blew up.
// Fix: isolate the SCRIPT TAG that contains outbound_click, then take its body.
// Anchoring on the marker first is what makes this correct rather than lucky.
const marker = html.indexOf("outbound_click");
if (marker === -1) {
  console.error("❌ `outbound_click` not found in built HTML — the GA4 partial did not render");
  process.exit(1);
}
const scriptStart = html.lastIndexOf("<script", marker);
const scriptEnd = html.indexOf("</script>", marker);
if (scriptStart === -1 || scriptEnd === -1) {
  console.error("❌ could not locate the script tag containing outbound_click");
  process.exit(1);
}
const scriptBody = html.slice(html.indexOf(">", scriptStart) + 1, scriptEnd).trim();

if (!/^\(function\s*\(\s*\)\s*\{/.test(scriptBody)) {
  console.error("❌ outbound tracker is not wrapped in an IIFE as expected");
  process.exit(1);
}
if (!/\(\)\s*;?$/.test(scriptBody)) {
  console.error("❌ outbound tracker IIFE appears truncated");
  process.exit(1);
}
const m = [scriptBody];

let fired = [];
global.window = {
  location: {
    href: "https://traindecade.com/posts/whey-vs-beef-protein/",
    hostname: "traindecade.com",
    pathname: "/posts/whey-vs-beef-protein/",
  },
};
global.document = {
  documentElement: { lang: "en" },
  addEventListener: (type, fn) => {
    if (type === "click") global.__handler = fn;
  },
};
global.gtag = (...args) => fired.push(args);

eval(m[0]);

if (typeof global.__handler !== "function") {
  console.error("❌ handler never registered a click listener");
  process.exit(1);
}

let fail = 0;
function t(label, href, expectFire, expectDomain, dataGa) {
  fired = [];
  global.__handler({
    target: {
      tagName: "A",
      href,
      textContent: "GainCut",
      parentElement: null,
      // ⚠️ 2026-11-26: the tracker now reads a `data-ga` attribute to fire a
      // per-link named event. Without this stub it threw "getAttribute is not a
      // function" on every case — the harness tested a version of the script that
      // no longer exists. A stub must model the DOM the real script actually uses.
      getAttribute: (name) => {
        if (name === "data-ga") return dataGa || null;
        if (name === "data-ga-location") return dataGa ? "test" : null;
        return null;
      },
    },
  });
  const didFire = fired.length > 0;
  let ok = didFire === expectFire;
  let domain = "";
  if (didFire) {
    domain = fired[0][2].link_domain;
    if (expectDomain && domain !== expectDomain) ok = false;
    // If data-ga was supplied, the SECOND event must carry that name.
    if (dataGa) {
      if (fired.length !== 2 || fired[1][1] !== dataGa) ok = false;
    }
  }
  if (!ok) fail++;
  console.log(
    `${ok ? "✅" : "❌"} ${label}: fired=${didFire} expected=${expectFire}` +
      (didFire ? ` domain=${domain}` : "")
  );
}

t("App Store HK link", "https://apps.apple.com/hk/app/gaincut/id6785259813", true, "apps.apple.com");
t("App Store US locale", "https://apps.apple.com/us/app/gaincut/id123", true, "apps.apple.com");
t("Product page", "https://ideafactory.one/gaincut/", true, "ideafactory.one");
t("Internal navigation (must not fire)", "https://traindecade.com/posts/other/", false);
t("Untracked external", "https://twitter.com/someone", false);
t("Relative link", "/posts/foo/", false);
// The data-ga path: an external link with a named event must fire outbound_click
// AND the named event, and the name must come from the attribute (not hardcoded).
t("Product page with data-ga", "https://ideafactory.one/gaincut/", true, "ideafactory.one", "gaincut_click");

console.log(fail === 0 ? "\nALL PASS" : `\n${fail} FAILED`);
process.exit(fail === 0 ? 0 : 1);
