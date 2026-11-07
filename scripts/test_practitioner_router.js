/* Maths harness for practitioner-router.js — no browser needed.
 * Asserts every input combination maps to the route the PROSE states, and that
 * no forbidden surface (form / email / fetch) exists in the source.
 */
const fs = require("fs");
const path = "/Users/home/Projects/traindecade-web/assets/js/practitioner-router.js";
const src = fs.readFileSync(path, "utf8");

// ---- scope guards: the forbidden things must be absent -------------------
const forbidden = [
  ["fetch(", "network call"],
  ["XMLHttpRequest", "network call"],
  ["type=\"email\"", "email field"],
  ["localStorage", "storage"],
  ["sessionStorage", "storage"],
  ["<form", "form element"],
];
let scopeFail = 0;
for (const [needle, label] of forbidden) {
  if (src.includes(needle)) {
    console.log(`❌ FORBIDDEN: found ${label} (${needle}) in widget source`);
    scopeFail++;
  }
}
if (!scopeFail) console.log("✅ scope guards clean — no fetch/XHR/email/storage/form");

// ---- minimal DOM shim ----------------------------------------------------
const els = {};
function mk(tag) {
  return {
    tag, textContent: "", innerHTML: "", hidden: true, value: "",
    _attrs: {}, _listeners: {},
    setAttribute(k, v) { this._attrs[k] = v; },
    getAttribute(k) { return this._attrs[k]; },
    addEventListener(ev, fn) { (this._listeners[ev] = this._listeners[ev] || []).push(fn); },
    dispatch(ev) { (this._listeners[ev] || []).forEach((f) => f()); },
  };
}
const root = mk("div");
root.setAttribute("data-lang", "en");
root.setAttribute("data-source-post", "who-can-actually-help-you");
const outEl = mk("div");
const btn = mk("button");
root.setAttribute("data-lang","en");els[".prac-router"] = root;
els["#pr-out"] = outEl;
els["#pr-run"] = btn;

let checked = {}; // name -> value
const radios = [];
for (let q = 1; q <= 4; q++) {
  for (const v of ["redflag", "timing", "constant", "local", "nerve", "neuro", "none", "passive", "active", "na"]) {
    const r = mk("input");
    r._name = `pr-q${q}`;
    r._value = v;
    radios.push(r);
  }
}

global.document = {
  readyState: "complete",
  querySelector(sel) {
    if (els[sel]) return els[sel];
    // selector is input[name="pr-qN"]:checked
    if (sel.indexOf("pr-q") !== -1) {
      const name = sel.slice(sel.indexOf("pr-q"), sel.indexOf("pr-q") + 5);
      const val = checked[name];
      if (!val) return null;
      const found = radios.find((r) => r._name === name && r._value === val) || null;
      if (found) found.value = found._value; // widget reads el.value
      return found;
    }
    return null;
  },
  querySelectorAll() { return radios; },
  getElementById(id) { return els["#" + id] || null; },
  addEventListener() {},
};
global.window = { gtag: null };

eval(src);

// ---- expected decision table, transcribed from the POST's prose ----------
// Prose rules, in order:
//   1 red flag (night pain / fever / weight loss) -> prompt clinical assessment
//   2 numbness, weakness, bladder/bowel -> diagnosis by clinician first
//   3 already doing active loading and progressing -> STAY, don't switch
//   4 localized + time-of-day driven -> loading prescription; foot -> podiatrist
//   5 localized, no timing -> MSK physio
function expected(q1, q2, q3, q4) {
  if (q1 === "redflag") return "urgent";
  if (q3 === "neuro") return "neuro";
  if (q4 === "active") return "stay";
  if (q2 === "local" && q1 === "timing") return "podiatry";
  if (q2 === "local") return "physio";
  if (q2 === "nerve") return "neuro";
  return "physio";
}

const q1v = ["redflag", "timing", "constant"];
const q2v = ["local", "nerve"];
const q3v = ["neuro", "none"];
const q4v = ["passive", "active", "na"];

let fails = 0, n = 0;
const seen = new Set();
for (const a of q1v) for (const b of q2v) for (const c of q3v) for (const d of q4v) {
  n++;
  checked = { "pr-q1": a, "pr-q2": b, "pr-q3": c, "pr-q4": d };
  outEl.hidden = true;
  outEl.innerHTML = "";
  btn.dispatch("click");
  const html = outEl.innerHTML;
  if (outEl.hidden) { console.log(`❌ no output for ${a}/${b}/${c}/${d}`); fails++; continue; }
  const want = expected(a, b, c, d);
  // recover which ROUTES entry rendered by matching its label
  const map = {
    urgent: "See a clinician promptly",
    neuro: "A clinician for diagnosis first",
    podiatry: "A podiatrist or foot",
    physio: "A musculoskeletal physiotherapist",
    stay: "Stay with the plan you have",
  };
  const got = Object.keys(map).find((k) => html.includes(map[k]));
  seen.add(want);
  if (got !== want) {
    console.log(`❌ MISMATCH ${a}/${b}/${c}/${d}: want ${want}, got ${got}`);
    fails++;
  }
}

console.log(`\n${fails === 0 ? "✅" : "❌"} ${n - fails}/${n} input combinations route correctly`);
console.log(`   routes reachable: ${[...seen].sort().join(", ")}`);
const allRoutes = ["urgent", "neuro", "podiatry", "physio", "stay"];
const unreachable = allRoutes.filter((r) => !seen.has(r));
if (unreachable.length) console.log(`   ⚠️ UNREACHABLE: ${unreachable.join(", ")}`);

// ---- incomplete answers must not render a verdict -----------------------
checked = { "pr-q1": "timing", "pr-q2": "local" };
outEl.hidden = true; outEl.innerHTML = "";
btn.dispatch("click");
const warned = outEl.innerHTML.includes("pr-warn") && !outEl.hidden;
console.log(`${warned ? "✅" : "❌"} incomplete answers prompt rather than guess`);

// ---- ZH renders ZH strings ----------------------------------------------
// The widget captures its language at INIT (correct: a page doesn't switch
// language mid-session), so ZH must be tested in a FRESH evaluation.
root.setAttribute("data-lang", "zh");
checked = { "pr-q1": "timing", "pr-q2": "local", "pr-q3": "none", "pr-q4": "passive" };
outEl.hidden = true; outEl.innerHTML = "";
btn._listeners = {};
eval(src);          // re-init with lang=zh
btn.dispatch("click");
const zhOk = outEl.innerHTML.indexOf("足病診療師") !== -1 &&
             outEl.innerHTML.indexOf("你的路徑") !== -1;
console.log(`${zhOk ? "✅" : "❌"} ZH locale renders ZH verdict text`);

process.exit(fails === 0 && warned && zhOk && scopeFail === 0 ? 0 : 1);
