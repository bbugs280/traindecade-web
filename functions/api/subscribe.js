/**
 * /api/subscribe — Cloudflare Pages Function
 *
 * PURPOSE: capture email on the ZH post template without shipping the
 * MailerLite API token to the browser.
 *
 * ⚠️ WHY THIS IS A SERVER FUNCTION AND NOT AN EMBED (decided 2026-11-23)
 *   A MailerLite "embedded form" would put the group ID and post target in
 *   page source and, worse, gives NO per-post attribution — you would learn
 *   "someone subscribed", never "which article converted them". The whole
 *   point of this card is attribution: traindecade's ZH lane is the only
 *   channel with measured demand (20 clicks / 90d, pos 5.4), and we need to
 *   know which post turns a reader into a subscriber.
 *   So the form POSTs {email, slug} here; we forward to MailerLite and stamp
 *   the source post into the subscriber's fields.
 *
 * ⚠️ THE TOKEN NEVER REACHES THE BROWSER.
 *   It lives in the Cloudflare Pages environment variable MAILERLITE_API_TOKEN
 *   (Settings → Environment variables → Production, encrypted). Never in a
 *   Hugo layout, never in git, never in a `?api_key=` query string.
 *
 * ⚠️ WHY WE DO NOT FIRE-AND-FORGET (waitUntil) FOR THE SUBSCRIBE CALL:
 *   The AI-crawler logger can fire-and-forget because losing a log row costs
 *   nothing. Losing a SUBSCRIBER costs a human who wanted to hear from us.
 *   The user must see a real success or a real error, so we await and report.
 *
 * ENV REQUIRED:
 *   MAILERLITE_API_TOKEN  (secret; account-scoped, MailerLite → Integrations → API)
 *   MAILERLITE_GROUP_ID   (plain var; 204928889296782726 = group "traindecade")
 */

const MAILERLITE_ENDPOINT = "https://connect.mailerlite.com/api/subscribers";

// Deliberately simple. A strict RFC-5322 regex rejects addresses real people
// have; a permissive one lets junk through. This sits in between and the real
// validator is MailerLite's own API, which will reject what it cannot deliver.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      // The form is same-origin; no need for permissive CORS.
      "cache-control": "no-store",
    },
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  // ---- Parse -----------------------------------------------------------
  let payload;
  try {
    // Accept both JSON (fetch) and urlencoded (a no-JS form fallback).
    const ct = request.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      payload = await request.json();
    } else {
      const fd = await request.formData();
      payload = Object.fromEntries(fd.entries());
    }
  } catch (e) {
    return json({ ok: false, error: "bad_request" }, 400);
  }

  const email = String(payload.email || "").trim().toLowerCase();
  // ⚠️ slug is UNTRUSTED and lands in a MailerLite field, so it is sanitised to
  // a slug charset and length-capped. An unsanitised slug is an injection
  // vector into someone else's dashboard.
  const slug = String(payload.slug || "unknown")
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "")
    .slice(0, 80) || "unknown";

  if (!EMAIL_RE.test(email)) {
    return json({ ok: false, error: "invalid_email" }, 400);
  }

  // ---- Config guard ----------------------------------------------------
  // ⚠️ Fail LOUDLY (500) rather than silently pretending success. A missing
  // token that returns {ok:true} is the exact class of silent failure this
  // session already found twice — a form that looks like it works and
  // collects nobody.
  if (!env.MAILERLITE_API_TOKEN || !env.MAILERLITE_GROUP_ID) {
    console.error("subscribe: MAILERLITE_API_TOKEN or MAILERLITE_GROUP_ID missing");
    return json({ ok: false, error: "not_configured" }, 500);
  }

  // ---- Forward to MailerLite -------------------------------------------
  let upstream;
  try {
    upstream = await fetch(MAILERLITE_ENDPOINT, {
      method: "POST",
      headers: {
        authorization: `Bearer ${env.MAILERLITE_API_TOKEN}`,
        "content-type": "application/json",
        accept: "application/json",
      },
      body: JSON.stringify({
        email,
        groups: [env.MAILERLITE_GROUP_ID],
        // `fields` must already exist in the MailerLite account or the API
        // rejects the whole request. `source_post` is created for this feature.
        fields: { source_post: slug },
        // ⚠️ status "active" = double opt-in OFF. Vincent's call: this is a
        // blog capture with low volume, and a confirmation email is a second
        // barrier between a reader and a promise. If deliverability ever
        // suffers, flip to "unconfirmed" and MailerLite sends the opt-in.
        status: "active",
      }),
    });
  } catch (e) {
    console.error("subscribe: network error", e && e.message);
    return json({ ok: false, error: "upstream_unreachable" }, 502);
  }

  // ---- Interpret -------------------------------------------------------
  // 200 = created or updated. 422 = MailerLite rejected the payload
  // (commonly a `fields` key that does not exist in the account yet).
  if (upstream.status === 200 || upstream.status === 201) {
    return json({ ok: true });
  }

  let detail = "";
  try {
    const body = await upstream.text();
    detail = body.slice(0, 300);
    console.error(`subscribe: mailerlite ${upstream.status} ${detail}`);
  } catch (_) {
    /* body already consumed or unreadable; status is enough */
  }

  // ⚠️ Do NOT leak the upstream body to the browser — it can echo the request
  // back, and the request contained the token in a header on some error paths.
  return json({ ok: false, error: "upstream_error" }, 502);
}

// A GET to this path is almost certainly a misconfigured form. Say so plainly
// instead of returning the default HTML 404, which reads like a routing bug.
export async function onRequestGet() {
  return json({ ok: false, error: "method_not_allowed" }, 405);
}
