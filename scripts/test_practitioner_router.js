/* Maths harness for practitioner-router.js — no browser needed.
 * Asserts every input combination maps to the route the PROSE states, and that
 * no forbidden surface (form / email / fetch) exists in the source.
 *
 * ⚠️ Routing inputs are SYMPTOM facts only. Treatment history (q4) selects
 * between "stay" and "carry on", never a practitioner type. Do not reintroduce
 * a history-driven practitioner route: what you already tried does not tell you
 * which tissue is injured.
 */
const fs = require("fs");
const path = "/Users/home/Projects/traindecade-web/assets/js/practitioner-router.js";
const src = fs.readFileSync(path, "utf8");

// ---- scope guards: the forbidden things must be absent -------------------
const forbidden = [
  ["fetch(", "network call"],
  ["XMLHttpRequest", "network call"],
  ['type="email"', "email field"],
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
els[".prac-router"] = root;
els["#pr-out"] = outEl;
els["#pr-run"] = btn;

let checked = {};
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

// ---- expected table, matches the post's prose ----------------------------
// 1 red flag                        -> urgent
// 2 numbness / weakness / bladder   -> neuro
// 3 already loading and progressing -> stay
// 4 burning / electric / spreading  -> neuro
// 5 anything else (sharp, one spot) -> physio
function expected(q1, q2, q3, q4) {
  if (q1 === "redflag") return "urgent";
  if (q3 === "neuro") return "neuro";
  if (q4 === "active") return "stay";
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
  const map = {
    urgent: "See a clinician",
    neuro: "A clinician for diagnosis first",
    physio: "A physiotherapist",
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
const allRoutes = ["urgent", "neuro", "physio", "stay"];
const unreachable = allRoutes.filter((r) => !seen.has(r));
if (unreachable.length) console.log(`   ⚠️ UNREACHABLE: ${unreachable.join(", ")}`);

// ---- the removed history-route must NOT come back ------------------------
// q4=passive + q1=timing + q2=local + q3=none used to route to "podiatry".
// It must now go to physio: history cannot select a practitioner type.
checked = { "pr-q1": "timing", "pr-q2": "local", "pr-q3": "none", "pr-q4": "passive" };
outEl.hidden = true; outEl.innerHTML = "";
btn.dispatch("click");
const noHistoryRoute = outEl.innerHTML.includes("A physiotherapist") &&
                       !outEl.innerHTML.includes("podiatrist or foot");
console.log(`${noHistoryRoute ? "✅" : "❌"} treatment history does not select a practitioner type`);

// ---- incomplete answers must not render a verdict -----------------------
checked = { "pr-q1": "timing", "pr-q2": "local" };
outEl.hidden = true; outEl.innerHTML = "";
btn.dispatch("click");
const warned = outEl.innerHTML.includes("pr-warn") && !outEl.hidden;
console.log(`${warned ? "✅" : "❌"} incomplete answers prompt rather than guess`);

// ---- ZH renders ZH strings (fresh eval: lang is fixed at init) ----------
root.setAttribute("data-lang", "zh");
checked = { "pr-q1": "timing", "pr-q2": "local", "pr-q3": "none", "pr-q4": "passive" };
outEl.hidden = true; outEl.innerHTML = "";
btn._listeners = {};
eval(src);
btn.dispatch("click");
const zhOk = outEl.innerHTML.indexOf("物理治療師") !== -1 &&
             outEl.innerHTML.indexOf("你的路徑") !== -1;
console.log(`${zhOk ? "✅" : "❌"} ZH locale renders ZH verdict text`);

// ---- no jargon in user-facing strings -----------------------------------
const jargon = ["pathoanatomical", "radicular", "dermatome", "proprioception",
                "modalities", "orthoses", "nociceptive", "etiology", "idiopathic",
                "tendinopathy", "musculoskeletal physiotherapist", "loading prescription"];
const hits = jargon.filter((j) => src.toLowerCase().includes(j));
console.log(hits.length
  ? `❌ JARGON in widget strings: ${hits.join(", ")}`
  : "✅ no jargon in widget strings");

process.exit(fails === 0 && warned && zhOk && noHistoryRoute && scopeFail === 0 && hits.length === 0 ? 0 : 1);
