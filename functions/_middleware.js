/**
 * AI Crawler Logger — Cloudflare Pages Function (middleware)
 *
 * PURPOSE: Cloudflare Pages produces no access logs, so AI crawler fetches are
 * invisible. This middleware runs on every request to the deployed site,
 * identifies AI/LLM crawlers by User-Agent, records each fetch to D1, and
 * passes the request through untouched. No HTML rewriting, no JS injection.
 *
 * ⚠️ WHY `functions/_middleware.js` AND NOT `_worker.js` (learned 2026-11-14):
 *   A `_worker.js` in the output root reported "Compiled Worker successfully"
 *   on every deploy but NEVER registered as a Pages Function. Proven by:
 *     - `wrangler pages deployment tail` → "does not have a Pages Function,
 *        you cannot tail a static site"
 *     - tail produced zero lines across 3 live requests
 *     - `/_worker.js` returned 404 (stripped, not served, not registered)
 *   `_middleware.js` under `functions/` is the documented entrypoint and works
 *   in standard Pages mode where `_worker.js` is silently dropped.
 *   Do NOT move this back to `_worker.js`.
 *
 * ⚠️ WHY IT MUST NOT `fetch(request)` BLINDLY:
 *   Re-fetching the same URL re-enters Cloudflare and loops (error 1042).
 *   We serve assets via env.ASSETS instead, which resolves inside the
 *   deployment with no network hop.
 */

const BOT_SIGNATURES = [
  ["OAI-SearchBot", /OAI-SearchBot/i],
  ["ChatGPT-User", /ChatGPT-User/i],
  ["GPTBot", /GPTBot/i],
  ["ClaudeBot", /ClaudeBot/i],
  ["Claude-User", /Claude-User/i],
  ["anthropic-ai", /anthropic-ai/i],
  ["PerplexityBot", /PerplexityBot/i],
  ["Perplexity-User", /Perplexity-User/i],
  ["Google-Extended", /Google-Extended/i],
  ["GoogleOther", /GoogleOther/i],
  ["BingBot", /bingbot/i],
  ["meta-externalagent", /meta-externalagent/i],
  ["Applebot-Extended", /Applebot-Extended/i],
  ["Amazonbot", /Amazonbot/i],
  ["Bytespider", /Bytespider/i],
  ["CCBot", /CCBot/i],
  ["cohere-ai", /cohere-ai/i],
  ["Diffbot", /Diffbot/i],
  ["YouBot", /YouBot/i],
  ["AI2Bot", /AI2Bot/i],
  ["Timpibot", /Timpibot/i],
  ["DuckAssistBot", /DuckAssistBot/i],
  ["MistralAI-User", /MistralAI-User/i],
];

function identifyBot(ua) {
  if (!ua) return null;
  for (const [name, re] of BOT_SIGNATURES) {
    if (re.test(ua)) return name;
  }
  return null;
}

/**
 * ⚠️ DUPLICATE-ROW GUARD (v2 — 2026-11-14)
 *
 * SYMPTOM: every crawler fetch logged TWICE — once as `traindecade.com`, once
 * as `traindecade.pages.dev`, ~2ms apart with near-identical timestamps.
 * Production evidence: PerplexityBot on /dedupe-probe-3/ recorded as
 *   00:55:07.742 pages.dev   +   00:55:07.748 traindecade.com
 *
 * FIRST ATTEMPT FAILED: an in-memory Map keyed on bot+path. Pages does not
 * preserve module-level state across requests, so the Map was always empty.
 * Do NOT reintroduce an in-memory guard here.
 *
 * THIS VERSION: the guard lives in D1, the only state that actually persists.
 * A UNIQUE index on (bot, path, ts_bucket) makes the second insert a no-op via
 * INSERT OR IGNORE. ts_bucket is the timestamp truncated to 10 seconds — far
 * wider than the 2ms duplicate gap, far narrower than two genuine crawler hits
 * on the same page.
 */
const DEDUPE_BUCKET_SECONDS = 10;

/** 2026-11-14T00:55:07.742Z -> 2026-11-14T00:55:00.000Z */
function tsBucket(iso) {
  const d = new Date(iso);
  d.setUTCSeconds(
    Math.floor(d.getUTCSeconds() / DEDUPE_BUCKET_SECONDS) * DEDUPE_BUCKET_SECONDS,
    0
  );
  return d.toISOString();
}

export async function onRequest(context) {
  // ⚠️ `ctx` DOES NOT EXIST in Pages Functions. The Service-Worker-style
  // `fetch(req, env, ctx)` signature gives you ctx; the Pages middleware
  // signature does NOT. Using context.ctx.waitUntil threw:
  //   TypeError: Cannot read properties of undefined (reading 'waitUntil')
  // Verified via `wrangler pages deployment tail` on 2026-11-14 — every
  // crawler request returned HTTP 500 while browsers stayed 200, because the
  // exception only fired on the logging branch.
  // `waitUntil` lives on the context object itself.
  const { request, env, waitUntil, next } = context;

  const ua = request.headers.get("user-agent") || "";
  const bot = identifyBot(ua);
  const url = new URL(request.url);

  // ⚠️ Use next(), NOT env.ASSETS.fetch(request).
  // `env.ASSETS` only exists in a `_worker.js` (Advanced Mode) deployment.
  // In Functions/middleware the documented way to reach the static asset is
  // next().
  const response = await next();

  if (bot && env.DB) {
    waitUntil(
      (async () => {
        try {
          const now = new Date().toISOString();
          // INSERT OR IGNORE + the unique index on (bot, path, ts_bucket)
          // is the whole dedupe mechanism. No application-side state.
          await env.DB.prepare(
            `INSERT OR IGNORE INTO ai_fetches
               (ts, host, bot, path, method, status, country, bytes, ua, ts_bucket)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
          )
            .bind(
              now,
              url.hostname,
              bot,
              url.pathname,
              request.method,
              response.status,
              (request.cf && request.cf.country) || "",
              response.headers.get("content-length") || "",
              ua.slice(0, 300),
              tsBucket(now)
            )
            .run();
        } catch (err) {
          // A logging failure must never break a page load.
          console.error("ai_fetches insert failed:", err && err.message);
        }
      })()
    );
  }

  return response;
}
