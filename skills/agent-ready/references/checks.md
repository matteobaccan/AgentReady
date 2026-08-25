# The checks, one by one

Every check the scanner runs: what it tests, what a pass looks like, how to fix
a failure, and where the spec lives. Check IDs match `agent_ready_scan.py`
output and the JSON report.

Statuses: **pass** · **fail** · **warn** (present but wrong) · **n/a** (not
applicable / informational) · **err** (could not test).

---

## Category 1 — Discoverability

### `robotsTxt` — robots.txt
*Probe:* `GET /robots.txt`. Pass needs HTTP 200, a non-HTML content type, and at
least one valid `User-agent:` group. A robots.txt served as HTML is a soft 404
and fails.

*Fix:* copy `assets/robots.txt`, replace `{{DOMAIN}}`, serve as
`text/plain; charset=utf-8`.

*Spec:* RFC 9309 — <https://www.rfc-editor.org/rfc/rfc9309.html>

### `sitemap` — XML sitemap
*Probe:* every `Sitemap:` directive in robots.txt, then `/sitemap.xml`,
`/sitemap-index.xml`, `/sitemap/sitemap.xml`. Pass needs a `<urlset>` or
`<sitemapindex>` document.

*Fix:* generate one (most frameworks and CMSs do this already), then **reference
it from robots.txt** — that is the half people forget. Keep `<lastmod>` honest:
agents use it to decide what to re-read.

*Spec:* <https://www.sitemaps.org/protocol.html>

### `linkHeaders` — Link response headers
*Probe:* `GET /`, read the `Link:` response header. Pass needs at least one
agent-relevant `rel`: `service-desc`, `describedby`, `api-catalog`,
`ai-catalog`, `alternate`, `canonical`, `license`, `author`.

*Why it matters:* an agent fetching your JSON API or a PDF never parses your
`<head>`. Headers travel with every response.

*Fix:* `assets/snippets/serving-recipes.md` §2.

*Spec:* RFC 8288 — <https://www.rfc-editor.org/rfc/rfc8288.html>

### `dnsAid` — DNS for AI Discovery
*Probe:* DNS-over-HTTPS for `SVCB`/`HTTPS`/`TXT` at `_index._agents.<domain>`,
`_a2a._agents.<domain>`, `_mcp._agents.<domain>` and `_agent.<domain>`, on both
the host and the apex.

*Result nuance:* a `SERVFAIL` (common with DNSSEC-less or slow resolvers) reports
**n/a**, not fail — absence of proof, not proof of absence.

*Fix:* only worth doing if you actually operate an agent or MCP endpoint. Then:

```
_mcp._agents.example.com. 3600 IN SVCB 1 mcp.example.com. alpn="h2" port=443
_index._agents.example.com. 3600 IN TXT "v=aid1; uri=https://example.com/.well-known/ai-catalog.json"
```

Sign the zone with DNSSEC — unsigned records give an agent nothing to trust.

*Spec:* <https://datatracker.ietf.org/doc/draft-mozleywilliams-dnsop-dnsaid/> ·
<https://aid.agentcommunity.org/docs/specification>

---

## Category 2 — Content Accessibility

### `markdownNegotiation` — Markdown for Agents
*Probe:* `GET /` with `Accept: text/markdown;q=1.0, text/plain;q=0.8,
text/html;q=0.1`. Pass needs `Content-Type: text/markdown` **and**
`Vary: Accept`. Markdown returned without `Vary: Accept` scores **warn** — a CDN
will eventually hand your markdown to a browser or your HTML to an agent.
An explicit `/page.md` route with no negotiation is also **warn**.

*Why it matters:* HTML costs an agent roughly 5× the tokens of the same content
as markdown, and navigation chrome, cookie banners and script tags crowd out
the part that mattered.

*Fix:* `assets/snippets/serving-recipes.md` §1. On Cloudflare it is a dashboard
toggle.

*Spec:* RFC 7763 (`text/markdown`) ·
<https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/>

---

## Category 3 — Bot Access Control

### `robotsTxtAiRules` — AI crawlers are covered
*Probe:* parse robots.txt for groups naming AI crawlers (GPTBot, ClaudeBot,
Google-Extended, CCBot, PerplexityBot, Bytespider, Applebot-Extended, …) or a
`User-agent: *` group.

*Result nuance:* a wildcard group **passes** — the point is that AI crawlers hit
a stated rule, not that you named each one. The scanner also reports which AI
bots you fully disallow, so you can confirm that was deliberate.

*Trap:* a bot that matches a named group ignores the wildcard group entirely.
If you add `User-agent: GPTBot`, repeat every directive you care about inside
it, `Content-Signal` included.

### `contentSignals` — Content Signals
*Probe:* `Content-Signal:` directives in robots.txt, read both as a directive
and inside comments.

*Values:* `search` (classic index: links and short excerpts), `ai-input`
(real-time grounding for generative answers, i.e. RAG), `ai-train` (training or
fine-tuning). Each is `yes` or `no`; omitting a key states no preference.

*Judgement call, not a default:* `search=yes, ai-input=yes, ai-train=no` is the
common stance for a site that wants to be cited but not absorbed. A docs site
that wants to be memorised by models sets `ai-train=yes`. Signals are a stated
preference with legal weight in some jurisdictions, not an enforcement
mechanism.

*Spec:* <https://contentsignals.org/> ·
<https://datatracker.ietf.org/doc/draft-romm-aipref-contentsignals/>

### `webBotAuth` — Web Bot Auth
*Probe:* `GET /.well-known/http-message-signatures-directory`, expect a JWKS.

*Informational.* This is for sites that **operate** a crawler or agent and want
origins to verify it cryptographically instead of trusting a User-Agent string.
Publishing nothing is normal and reports **n/a**.

*Spec:* RFC 9421 ·
<https://datatracker.ietf.org/doc/draft-meunier-web-bot-auth-architecture/>

---

## Category 4 — API, Auth & MCP Discovery

This is where most sites sit at zero, and where the biggest jump in the ladder
lives. You do **not** need all nine — **any one** of `apiCatalog`,
`mcpServerCard`, `a2aAgentCard` or `agentSkills` reaches level 4. Pick the one
that matches something the site already has; see `levels.md`.

### `apiCatalog` — API Catalog (RFC 9727)
*Probe:* `GET /.well-known/api-catalog` with
`Accept: application/linkset+json, application/json`. Pass needs a JSON object
with a `linkset` array.

*Fix:* `assets/well-known/api-catalog.json`. Serve it at
`/.well-known/api-catalog` **without the `.json` extension** and with
`Content-Type: application/linkset+json`.

*Spec:* <https://www.rfc-editor.org/rfc/rfc9727.html>

### `oauthDiscovery` — OAuth / OIDC discovery
*Probe:* `/.well-known/oauth-authorization-server`, then
`/.well-known/openid-configuration`. Pass needs `issuer` or
`authorization_endpoint`. The scanner also flags an `agent_auth` block, which is
what auth.md keys off.

*This is the level-5 gate* — the one check separating Agent-Integrated from
Agent-Native. But *skip it* if the site has no login: it is not a gap for a
content site, and there is no honest way to publish it without an
authorization server behind it.

*Spec:* RFC 8414 · OpenID Connect Discovery 1.0

### `oauthProtectedResource` — Protected Resource Metadata (RFC 9728)
*Probe:* `/.well-known/oauth-protected-resource`, plus a `WWW-Authenticate`
header carrying `resource_metadata`.

*Why it matters:* this is how an MCP client discovers which authorization server
guards your endpoint. If you ship an authenticated MCP server, this is not
optional — it is the handshake.

*Spec:* <https://www.rfc-editor.org/rfc/rfc9728.html>

### `authMd` — agent registration
*Probe:* `GET /auth.md` then `/.well-known/auth.md` with an `Accept` that
includes `text/markdown`. The scanner rejects a soft 404 (a body identical to
the homepage markdown) and requires the document to actually mention
registration, scopes or credentials.

*Fix:* `assets/auth.md`, paired with RFC 9728 metadata.

*Spec:* <https://github.com/workos/auth.md>

### `mcpServerCard` — MCP Server Card
*Probe:* `/.well-known/mcp.json`, `/.well-known/mcp/server-card.json`,
`/.well-known/mcp/server-cards.json`; then a live `initialize` POST to `/mcp`.
A live endpoint with no card scores **warn** — it works only for agents that
already know the URL.

*Fix:* `assets/well-known/mcp.json`. The `description` is what an agent reads to
decide whether to connect: describe the tools, not the company.

*Spec:* <https://modelcontextprotocol.io/> · SEP-2127

### `a2aAgentCard` — A2A Agent Card
*Probe:* `/.well-known/agent-card.json`, then `/.well-known/agent.json`.

*Only relevant if you run an agent* other agents should delegate to. For a
content site this is legitimately not applicable.

*Path note:* `/.well-known/agent.json` is the pre-v0.3 location. A card found
only there scores **warn**: it is real, but agents following the current spec
look at `agent-card.json` and will not find it.

*Spec:* <https://a2a-protocol.org/latest/specification/>

### `agentSkills` — Agent Skills index
*Probe:* `/.well-known/agent-skills/index.json`, then the legacy
`/.well-known/skills/index.json`. Pass needs a `skills` array with at least one
entry.

*What it is for:* publishing procedural knowledge — how to use your API, how to
format a submission, house style — that an agent loads on demand. Cheapest
high-value item on this list for a docs or API site.

*Fix:* `assets/well-known/agent-skills/index.json` plus one `SKILL.md` per skill.
Lead each description with the trigger ("Use when…"), because that line is what
an agent matches against.

*Spec:* <https://schemas.agentskills.io/discovery/0.2.0/schema.json>

### `webMcp` — WebMCP tools on the page
*Probe:* scan the homepage HTML for `document.modelContext` /
`navigator.modelContext` / `provideContext(` / `registerTool(`. With `--deep`,
also fetch up to 12 same-origin `<script src>` bundles.

*Known limit:* the reference scanner loads the page in a real browser. A static
scan misses tools registered by a bundle that our `--deep` pass did not reach.
Treat a fail here as "probably not, verify by hand" if you know you ship it.

*Fix:* `assets/snippets/webmcp.js`.

*Spec:* <https://github.com/webmachinelearning/webmcp> — note the getter moved
from `navigator` to `document` in the May 2026 draft.

### `ard` — Agentic Resource Discovery manifest
*Probe:* four mechanisms — `Agentmap:` in robots.txt, `<link rel="ai-catalog">`
in the head, `GET /.well-known/ai-catalog.json`, and DNS `TXT`/`SRV` at
`_catalog._agents` / `_search._agents`. Pass needs a manifest with an `entries`
array. Advertised-but-unfetchable scores **warn**.

*Why it matters:* ARD is the index that ties the rest together — one document
listing your MCP servers, A2A agents, skills and APIs. Published by Google,
Microsoft and Hugging Face in June 2026; v0.9 draft, Apache 2.0.

*Fix:* `assets/well-known/ai-catalog.json` + the `Agentmap:` line in
`assets/robots.txt`. Fill in `representativeQueries` — registries use them for
semantic indexing, and an entry without them is close to invisible.

*Spec:* <https://agenticresourcediscovery.org/spec/>

---

## Category 5 — Commerce

Scored only when the site looks transactional (Product/Offer JSON-LD, cart or
checkout routes, a known e-commerce platform). Otherwise every check reports
**n/a** and none of them affect the level.

| Check | Probe | What it is |
|---|---|---|
| `x402` | HTTP 402 on `/`, `/api`, `/api/v1`; `X-Payment` header | Per-call stablecoin payment over HTTP 402. Coinbase. |
| `mpp` | `/.well-known/mpp.json`, `/openapi.json` | Machine Payments Protocol. Stripe/Tempo, payment-method agnostic. |
| `ucp` | `/.well-known/ucp` | Universal Commerce Protocol. Google + Shopify, Etsy, Target, Walmart. Discover and check out across merchants. |
| `acp` | `/.well-known/acp.json` | Agentic Commerce Protocol. OpenAI + Stripe; behind ChatGPT Instant Checkout. |
| `ap2` | A2A Agent Card extensions | Agent Payments Protocol. Google. Proves an agent is authorised to pay; layers on A2A. |

**How to choose:** ACP if you want to sell inside ChatGPT. UCP if you want to
appear in Google's shopping surfaces. x402 or MPP if you are selling API calls
rather than goods. AP2 only if you already run an A2A agent. Picking all five is
a sign you have not picked.

---

## Extended track (not part of the 0–5 ladder)

Things agents rely on that the reference scanner does not score. Skip with
`--no-extended`.

| Check | Pass condition | Why it matters to an agent |
|---|---|---|
| `llmsTxt` | `/llms.txt` exists, has an H1, is not a soft 404 | Curated entry point: which pages are authoritative and in what order to read them. Late draft, no search-engine weight — value is the curation. |
| `structuredData` | JSON-LD on the homepage with a real `@type` (`@graph` supported) | Turns prose into facts an agent can quote without inference. |
| `htmlSemantics` | h1, `main`/`article`, meta description, canonical, `lang`, OpenGraph, `alt` on images | Cheap, and it is what an agent falls back to when there is no markdown route. |
| `serverRendered` | ≥250 words of text in the initial HTML | Most crawling agents never execute JavaScript. An empty shell is an empty page. |
| `transport` | HTTP 301/308 → HTTPS, `ETag` or `Last-Modified` present | Validators let an agent re-check cheaply instead of refetching everything. |
| `statusSanity` | a missing path returns a real 404 | Soft 404s teach an agent that every URL exists — it will hallucinate from your error page. |
| `securityTxt` | `/.well-known/security.txt` with a `Contact:` | Machine-readable escalation path. RFC 9116. |
| `feed` | RSS/Atom linked from `<head>` | The cheapest change-notification channel there is. |
