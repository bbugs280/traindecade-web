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

const BUILT = "/tmp/tdreview/public/posts/whey-vs-beef-protein/index.html";
if (!fs.existsSync(BUILT)) {
  console.error(`❌ ${BUILT} not found — run 'hugo' in the repo first.`);
  process.exit(1);
}

const html = fs.readFileSync(BUILT, "utf8");
const m = html.match(/\(function \(\) \{[\s\S]*?\}\)\(\);/);
if (!m) {
  console.error("❌ could not extract the inline outbound-tracking script from built HTML");
  process.exit(1);
}

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
function t(label, href, expectFire, expectDomain) {
  fired = [];
  global.__handler({
    target: { tagName: "A", href, textContent: "GainCut", parentElement: null },
  });
  const didFire = fired.length > 0;
  let ok = didFire === expectFire;
  let domain = "";
  if (didFire) {
    domain = fired[0][2].link_domain;
    if (expectDomain && domain !== expectDomain) ok = false;
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

console.log(fail === 0 ? "\nALL PASS" : `\n${fail} FAILED`);
process.exit(fail === 0 ? 0 : 1);
