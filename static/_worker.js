/**
 * AI Crawler Logger — Cloudflare Pages Worker (Advanced Mode)
 *
 * PURPOSE: GitHub Pages produces no access logs, so AI crawler fetches were
 * invisible. Cloudflare Pages runs this Worker natively on every request to
 * the deployed site, so bot fetches can be counted.
 *
 * ⚠️ WHY THIS LIVES IN THE SITE REPO, NOT AS AN EXTERNAL WORKER:
 *   A Pages custom domain is served from Cloudflare's asset layer BEFORE any
 *   external Worker route is evaluated, so an external Worker with a route of
 *   `traindecade.com/*` never fires. Verified empirically on 2026-11-13:
 *   responses carried `server: GitHub.com` with no `cf-ray` despite the route
 *   being attached. A `_worker.js` shipped INSIDE the Pages deployment is the
 *   supported way to run code on Pages requests.
 *
 * ⚠️ WHY IT MUST NOT `fetch(request)` BLINDLY:
 *   Re-fetching the same URL re-enters Cloudflare and loops (error 1042).
 *   We serve assets via env.ASSETS instead, which resolves inside the
 *   deployment with no network hop.
 *
 * Deploy: this file is placed in Hugo's `static/` dir, so `hugo` copies it to
 * `public/_worker.js` and `wrangler pages deploy public` ships it.
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

export default {
  async fetch(request, env, ctx) {
    const ua = request.headers.get("user-agent") || "";
    const bot = identifyBot(ua);
    const url = new URL(request.url);

    // Serve the static asset from within this deployment. No network hop,
    // so no possibility of re-entering Cloudflare and looping.
    const response = await env.ASSETS.fetch(request);

    if (bot && env.DB) {
      ctx.waitUntil(
        (async () => {
          try {
            await env.DB.prepare(
              `INSERT INTO ai_fetches
                 (ts, host, bot, path, method, status, country, bytes, ua)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
            )
              .bind(
                new Date().toISOString(),
                url.hostname,
                bot,
                url.pathname,
                request.method,
                response.status,
                (request.cf && request.cf.country) || "",
                response.headers.get("content-length") || "",
                ua.slice(0, 300)
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
  },
};
