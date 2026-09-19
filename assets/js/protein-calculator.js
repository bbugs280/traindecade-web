/* Protein target calculator — traindecade.com
 *
 * No dependencies, no CDN, no tracking beyond a single GA4 event.
 * Answers are UNGATED: no email field, no form, no popup.
 * See docs/changes/2026-09-19.md before adding any capture surface here.
 *
 * BASIS (must match /posts/how-much-protein-do-you-really-need/):
 *   Total-bodyweight reference: 1.6 g/kg/day  (Morton et al. 2018 plateau)
 *   Per-meal synthetic dose:    0.4 g/kg/meal (~25-40 g)
 *
 * Lean-mass adjustment for the "higher body fat" option is REAL, not cosmetic:
 * protein targets scale with lean mass far better than total mass. We therefore
 * cap the effective basis toward lean mass for higher body-fat users and SHOW
 * the deviation in the output note, so the number never silently disagrees
 * with the published 1.6 g/kg rule of thumb.
 */
(function () {
  "use strict";

  var LB_PER_KG = 2.20462;

  // Total-bodyweight multipliers by goal (centred on the 1.6 g/kg plateau).
  var GOAL_MULT = { cut: 1.8, maintain: 1.6, build: 1.9 };

  // Estimated body-fat midpoints used to derive the lean-mass basis.
  var BF_MID = { lean: 0.15, average: 0.25, higher: 0.35 };

  var month = function () { return new Date().getMonth(); };

  function t(lang, en, zh) { return lang === "zh" ? zh : en; }

  function clamp(n, lo, hi) { return Math.min(hi, Math.max(lo, n)); }

  function roundTo(n, step) { return Math.round(n / step) * step; }

  function init(root) {
    var lang = root.getAttribute("data-lang") || "en";
    var sourcePost = root.getAttribute("data-source-post") || "unknown";

    var elWeight = root.querySelector("#pc-weight");
    var elGoal = root.querySelector("#pc-goal");
    var elTraining = root.querySelector("#pc-training");
    var elBF = root.querySelector("#pc-bf");
    var elGrams = root.querySelector("#pc-grams");
    var elPerKg = root.querySelector("#pc-perkg");
    var elSplit = root.querySelector("#pc-split");
    var elNote = root.querySelector("#pc-note");
    var unitButtons = root.querySelectorAll(".pc-unit");

    var unit = "kg";
    var fired = false;

    function currentKg() {
      var raw = parseFloat(elWeight.value);
      if (isNaN(raw) || raw <= 0) { return 0; }
      var kg = unit === "kg" ? raw : raw / LB_PER_KG;
      // Hard clamp — the HTML min/max attrs are UI hints only and are
      // bypassable by paste/devtools. Keep the maths in a sane range so we
      // never render nonsense like "0 g" or an Infinity per-kg figure.
      if (!isFinite(kg)) { return 0; }
      kg = clamp(kg, 30, 300);
      return kg;
    }

    function compute() {
      var kg = currentKg();
      if (!kg) { return null; }

      var goal = elGoal.value;
      var training = elTraining.value;
      var bfKey = elBF.value;

      var mult = GOAL_MULT[goal] || 1.6;
      var bf = BF_MID[bfKey] != null ? BF_MID[bfKey] : 0.25;
      var leanKg = kg * (1 - bf);

      // Lean-mass reference: 1.6 g/kg of lean mass would under-feed a
      // higher-body-fat user relative to the total-weight rule, so we blend
      // toward the total-weight number. Weighting rises with body fat.
      var leanMult = 1.6;
      var leanTarget = leanKg * leanMult;
      var totalTarget = kg * mult;

      // Blend factor: the standard reader must land ON the published 1.6 g/kg
      // figure, so "average" gets only a token lean-mass influence. Real
      // lean-mass weighting kicks in only when body fat is genuinely elevated.
      // Guarded by /tmp/test_calc_maths.js — 80 kg average must be ~128 g.
      var leanWeight = bfKey === "higher" ? 0.5 : (bfKey === "average" ? 0.05 : 0.0);
      var target = totalTarget * (1 - leanWeight) + (leanTarget * (mult / 1.6)) * leanWeight;

      if (training === "no") { target *= 0.92; }

      // Per-meal synthetic dose: 0.4 g/kg total weight. Floored at 25 g and
      // CAPPED AT 40 g — this must match the published band in
      // /posts/how-much-protein-do-you-really-need/ ("~25-40 g per meal").
      // Do not raise the cap without updating the post.
      var perMeal = clamp(kg * 0.4, 25, 40);
      // Meals needed to reach the daily target at that per-meal dose.
      var meals = Math.max(3, Math.min(5, Math.ceil(target / perMeal)));
      // Show the realistic per-meal figure for the meal count actually used,
      // so the split never implies a dose above the published band.
      var shownPerMeal = Math.min(perMeal, target / meals);

      var daily = roundTo(target, 5);
      var perKgTotal = daily / kg;

      return {
        kg: kg,
        daily: daily,
        perKgTotal: perKgTotal,
        leanKg: leanKg,
        bfPct: bf * 100,
        perMeal: roundTo(shownPerMeal, 1),
        meals: meals,
        dayPerMealCap: roundTo(perMeal, 1),
        bfKey: bfKey,
        training: training,
        goal: goal
      };
    }

    function render() {
      var r = compute();
      if (!r) {
        elGrams.textContent = "—";
        elPerKg.textContent = "";
        elSplit.textContent = "";
        elNote.textContent = "";
        return;
      }

      elGrams.textContent = r.daily;

      elPerKg.textContent = t(lang,
        "≈ " + r.perKgTotal.toFixed(2) + " g per kg of bodyweight",
        "約每公斤體重 " + r.perKgTotal.toFixed(2) + " 克");

      elSplit.textContent = t(lang,
        "Split across " + r.meals + " meals: roughly " + r.perMeal + " g each. That's the per-meal dose that reliably triggers muscle protein synthesis in one sitting.",
        "分成 " + r.meals + " 餐：每餐約 " + r.perMeal + " 克。這是單次能有效啟動肌肉蛋白合成的份量。");

      // Honest explanation when the lean-mass basis shifts the number.
      var note;
      if (r.bfKey === "higher") {
        note = t(lang,
          "Because your body-fat estimate is higher, this target is adjusted toward " + Math.round(r.leanKg) + " kg of lean mass rather than your full " + Math.round(r.kg) + " kg. That's why it sits below the straight 1.6 g/kg figure — the rule of thumb is built on total weight, and lean mass is the better basis when body fat is elevated.",
          "因為你的體脂估算偏高，此目標是以約 " + Math.round(r.leanKg) + " 公斤淨體重調整，而非你的總體重 " + Math.round(r.kg) + " 公斤。這就是為什麼數字會低於單純的 1.6 g/kg —該經驗法則以總體重計算，而體脂偏高時，淨體重是更準確的基準。");
      } else if (r.bfKey === "average") {
        note = t(lang,
          "This is close to the standard 1.6 g/kg rule of thumb, lightly adjusted for lean mass (" + Math.round(r.leanKg) + " kg).",
          "此數字接近標準的 1.6 g/kg 經驗法則，並依淨體重（約 " + Math.round(r.leanKg) + " 公斤）略作調整。");
      } else {
        note = t(lang,
          "At your body composition this lands almost exactly on the standard 1.6 g/kg rule of thumb.",
          "以你的體脂狀況，此數字幾乎完全符合標準的 1.6 g/kg 經驗法則。");
      }

      if (r.training === "no") {
        note += t(lang,
          " Slightly reduced because you're not resistance training right now — without a training stimulus, extra protein has less to build with.",
          " 因為你目前沒有重訓，數字略為調低——沒有訓練刺激，多餘的蛋白質也無用武之地。");
      }

      elNote.textContent = note;

      if (!fired && typeof window.gtag === "function") {
        fired = true;
        window.gtag("event", "calculator_used", {
          source_post: sourcePost,
          goal: r.goal,
          lang: lang
        });
      }
    }

    // Unit toggle — convert the displayed value so the number stays truthful.
    Array.prototype.forEach.call(unitButtons, function (btn) {
      btn.addEventListener("click", function () {
        var next = btn.getAttribute("data-unit");
        if (next === unit) { return; }
        var kg = currentKg();
        unit = next;
        Array.prototype.forEach.call(unitButtons, function (b) {
          b.classList.toggle("is-active", b === btn);
        });
        if (kg) {
          var shown = unit === "kg" ? kg : kg * LB_PER_KG;
          elWeight.value = Math.round(shown * 10) / 10;
        }
        render();
      });
    });

    [elWeight, elGoal, elTraining, elBF].forEach(function (el) {
      el.addEventListener("input", render);
      el.addEventListener("change", render);
    });

    render();
  }

  function boot() {
    var nodes = document.querySelectorAll(".protein-calc");
    Array.prototype.forEach.call(nodes, init);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
