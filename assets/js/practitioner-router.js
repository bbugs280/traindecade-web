/* Practitioner Router — vanilla IIFE, no dependencies, no network calls.
 *
 * Routing logic must stay consistent with the prose in
 * /posts/who-can-actually-help-you/ (four questions -> one route).
 *
 * ⚠️ SCOPE GUARD: no form submission, no fetch/XHR, no email field, no storage.
 * The whole thing is a pure client-side lookup. If a later change adds any of
 * those, it is a scope violation, not a tweak.
 */
(function () {
  "use strict";

  var ROUTES = {
    urgent: {
      en: {
        label: "See a clinician — this needs a proper look",
        who: "A doctor, within days rather than weeks.",
        why: "Something on your list needs checking rather than loading: night pain that wakes you, fever, unexplained weight loss, or numbness/weakness/bladder or bowel change. These override every rule below. They are also the one situation where imaging is genuinely useful.",
        ask: "Ask for a diagnosis from examination, and ask whether imaging is indicated — rather than requesting a scan."
      },
      zh: {
        label: "去看醫生——這個需要認真檢查",
        who: "醫生，幾天內，而不是幾星期後。",
        why: "你的清單上有需要檢查而不是負荷的項目：痛到醒、發燒、不明原因體重下降，或麻／無力／大小便改變。這些優先於以下所有規則。這也是影像檢查真正有用的唯一情況。",
        ask: "要求靠身體檢查做診斷，並問影像是否有需要——而不是自己指定要拍片。"
      }
    },
    neuro: {
      en: {
        label: "A clinician for diagnosis first, then a physiotherapist",
        who: "Sports medicine physician or orthopaedic specialist → then an MSK physiotherapist.",
        why: "Numbness or weakness means a nerve may be involved. That needs a diagnosis before you load anything, because the loading plan for a nerve is different from the one for a tendon.",
        ask: "Ask which nerve the finding points to, and what would change the plan."
      },
      zh: {
        label: "先由臨床醫生診斷，再由物理治療師接手",
        who: "運動醫學醫生或骨科專科 → 然後是肌肉骨骼物理治療師。",
        why: "麻或無力代表可能牽涉神經。那需要在開始任何負荷之前先有診斷，因為神經的負荷計劃與肌腱不同。",
        ask: "問這個發現指向哪一條神經，以及什麼情況會改變方案。"
      }
    },
    physio: {
      en: {
        label: "A physiotherapist — and ask for a loading plan",
        who: "A physiotherapist who treats muscle and joint problems, and who gives you homework.",
        why: "Sharp pain in one spot, with a clear pattern and no nerve signs, is a loading problem. The fix is a plan that gets harder over time — not another course of hands-on treatment. For a foot or heel problem, a podiatrist is the alternative first call if you also need arch support.",
        ask: "Ask what the active half of the plan is, and how it progresses over twelve weeks."
      },
      zh: {
        label: "物理治療師——而且要一份負荷計劃",
        who: "處理肌肉關節問題、而且會給你回家功課的物理治療師。",
        why: "一點的銳痛、有明確規律、沒有神經徵象，就是負荷問題。解法是一份會越來越吃力的計劃，不是又一個被動療程。如果是足部或腳跟問題，而你同時需要足弓支撐，足病診療師是另一個合適的第一站。",
        ask: "問方案裡主動的那一半是什麼，以及它如何在十二週內漸進。"
      }
    },
    stay: {
      en: {
        label: "Stay with the plan you have — change nothing for twelve weeks",
        who: "The practitioner you are already seeing.",
        why: "You are already doing active loading and it is progressing. Rebuilding tissue takes months. Switching practitioners before then guarantees you never find out whether this plan was right. The commonest mistake at this stage is impatience, not the wrong therapist.",
        ask: "Ask for one measurable marker you can re-check at twelve weeks, so progress is a number rather than a feeling.",
        isStay: true
      },
      zh: {
        label: "留在你現有的方案——十二週內什麼都不要改",
        who: "你現在正在看的那一位。",
        why: "你已經在做主動負荷訓練，而且有進展。重建組織需要幾個月。在那之前換專業人士，保證你永遠不會知道這個方案對不對。這個階段最常見的錯誤是沒耐性，不是找錯治療師。",
        ask: "要求一個可以在十二週後重新量測的指標，讓進展是一個數字，而不是一種感覺。",
        isStay: true
      }
    }
  };

  /* Decision table — first match wins. Order matters: red flags first.
   *
   * ⚠️ Inputs are SYMPTOM facts only. What treatment you have already tried (q4)
   * does not tell you which tissue is injured, so it only routes between
   * "stay" and "not yet started" — it never selects a practitioner type.
   */
  function route(a) {
    if (a.q1 === "redflag") return "urgent";
    if (a.q3 === "neuro") return "neuro";
    if (a.q4 === "active") return "stay";
    if (a.q2 === "nerve") return "neuro";
    return "physio";
  }

  function collect() {
    var a = {};
    for (var i = 1; i <= 4; i++) {
      var el = document.querySelector('input[name="pr-q' + i + '"]:checked');
      if (!el) return null;
      a["q" + i] = el.value;
    }
    return a;
  }

  function stateFor(el) {
    return el && el.setAttribute ? el : null;
  }

  function render(outEl, key, lang) {
    var r = ROUTES[key][lang] || ROUTES[key].en;
    var t = lang === "zh"
      ? { route: "你的路徑", who: "看誰", why: "為什麼", ask: "預約時要問什麼", fallback: "請先回答全部四個問題。", track: "十二週後要問自己", trackBody: "在最近十二週持續而恰當的治療之後，有任何改變嗎？如果一個合理的治療已被正確執行三個月而毫無變化，診斷錯誤的可能性高於治療錯誤。要換的是做診斷的人，不是劑量。" }
      : { route: "Your route", who: "Who to see", why: "Why", ask: "What to ask at the appointment", fallback: "Please answer all four questions.", track: "Ask yourself at twelve weeks", trackBody: "Has anything changed after twelve weeks of consistent, appropriate treatment? If a plausible treatment has been done properly for three months with no change, the diagnosis is more likely wrong than the treatment. Change the diagnostician, not the dose." };

    var html = "";
    html += '<div class="pr-card' + (r.isStay ? " pr-card--stay" : "") + '">';
    html += '<p class="pr-kicker">' + t.route + "</p>";
    html += '<p class="pr-verdict">' + r.label + "</p>";
    html += '<dl class="pr-dl">';
    html += "<dt>" + t.who + "</dt><dd>" + r.who + "</dd>";
    html += "<dt>" + t.why + "</dt><dd>" + r.why + "</dd>";
    html += "<dt>" + t.ask + "</dt><dd>" + r.ask + "</dd>";
    html += "</dl>";
    html += "</div>";
    html += '<p class="pr-rule"><strong>' + t.track + ":</strong> " + t.trackBody + "</p>";

    outEl.innerHTML = html;
    outEl.hidden = false;
  }

  function init() {
    var root = document.querySelector(".prac-router");
    if (!root) return;
    var outEl = document.getElementById("pr-out");
    var btn = document.getElementById("pr-run");
    if (!outEl || !btn) return;

    var lang = root.getAttribute("data-lang") === "zh" ? "zh" : "en";

    btn.addEventListener("click", function () {
      var a = collect();
      if (!a) {
        outEl.innerHTML = '<p class="pr-warn">' +
          (lang === "zh" ? "請先回答全部四個問題。" : "Please answer all four questions.") +
          "</p>";
        outEl.hidden = false;
        return;
      }
      var key = route(a);
      render(outEl, key, lang);

      // GA4 event — attribution only, no personal data.
      try {
        if (typeof window.gtag === "function") {
          window.gtag("event", "router_used", {
            source_post: root.getAttribute("data-source-post") || "",
            route: key
          });
        }
      } catch (e) { /* analytics must never break the widget */ }
    });

    // Re-estimate as answers change, once a result is on screen.
    var inputs = document.querySelectorAll(".prac-router input[type=radio]");
    for (var i = 0; i < inputs.length; i++) {
      inputs[i].addEventListener("change", function () {
        if (!outEl.hidden) {
          var a2 = collect();
          if (a2) render(outEl, route(a2), lang);
        }
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
