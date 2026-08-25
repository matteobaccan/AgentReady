# The 0–5 ladder, and what to do at each rung

## The ladder

Each level requires everything below it. The rules below are implemented in
`compute_level()` in `scripts/agent_ready_scan.py`, and were derived by
scanning reference sites against Cloudflare's isitagentready.com until levels
and next-level requirements matched on all of them.

| Level | Name | Requires |
|---|---|---|
| **0** | Unprepared | — no valid robots.txt or no sitemap |
| **1** | Basic Web Presence | `robotsTxt` + `sitemap` |
| **2** | Bot-Aware | + `robotsTxtAiRules` + `contentSignals` |
| **3** | Agent-Readable | + `markdownNegotiation` |
| **4** | Agent-Integrated | + **any two** of `apiCatalog`, `mcpServerCard`, `agentSkills`, `webMcp`, `ard`, `oauthDiscovery` |
| **5** | Agent-Native | + `authMd` + `a2aAgentCard` |

Checks outside the ladder — `linkHeaders`, `dnsAid`, `webBotAuth`,
`oauthProtectedResource`, all commerce checks, the whole extended track — never
change the level. They are still worth fixing; the level is a floor, not a
score.

### Validation

| Site | This scanner | isitagentready.com |
|---|---|---|
| stripe.com | 1 Basic Web Presence, needs `contentSignals` | identical |
| www.baccan.it | 2 Bot-Aware, needs `markdownNegotiation` | identical |
| developers.cloudflare.com | 4 Agent-Integrated, needs `authMd` + `a2aAgentCard` | identical |
| isitagentready.com | 4 Agent-Integrated, needs `authMd` + `a2aAgentCard` | identical |

Re-verify at any time with `--remote`, which runs the official scan alongside
and prints both levels.

---

## What each rung actually buys you

**0 → 1 — be legible at all.** robots.txt and a sitemap. An agent that cannot
enumerate your pages treats your site as whatever it happened to land on.
Half an hour of work, and nothing downstream works without it.

**1 → 2 — state your terms.** Content Signals is the only place you get to say,
machine-readably, whether your content may be used for training, for grounding
generative answers, or only for classic search. Publishing nothing is not
neutrality — it leaves the decision entirely to the crawler.

**2 → 3 — stop making agents read HTML.** Markdown negotiation is the highest
value-per-hour item on the whole ladder: no new endpoint, no new protocol, one
server rule, and every agent that touches your site suddenly reads ~5× more of
your content within the same context budget. If you do exactly one thing from
this document, do this.

**3 → 4 — give agents something to call.** Two of six. For most sites the cheap
pair is `agentSkills` (procedural knowledge, just markdown files) plus `ard`
(one index JSON). If you already have an API, `apiCatalog` is nearly free. Ship
`mcpServerCard` only when there is a real MCP server behind it — a card pointing
at nothing is worse than no card.

**4 → 5 — let agents act on a user's behalf.** `auth.md` and an A2A Agent Card.
This is a product decision, not a config change: you are opening delegated,
credentialed access. For a content site, level 4 is a perfectly good ceiling and
level 5 would be theatre.

---

## Prioritising a real backlog

Sort by (impact ÷ effort), not by ladder order — apart from the fact that the
level itself only moves in ladder order.

**Tier 1 — hours, benefits every agent**
1. `robotsTxt` + `sitemap` + `contentSignals` — one file.
2. `markdownNegotiation` — one server rule.
3. `serverRendered`, `statusSanity`, `htmlSemantics` — if these fail, nothing
   above them matters, because the content an agent retrieves is empty or wrong.
4. `linkHeaders` — one header, and it reaches agents that never parse HTML.

**Tier 2 — a day, unlocks level 4**
5. `agentSkills` — write what your support team keeps re-explaining.
6. `ard` (`ai-catalog.json`) — the index that ties everything together.
7. `structuredData` — Organization + WebSite JSON-LD.
8. `llmsTxt` — curated reading order.

**Tier 3 — a project, only with a reason**
9. `mcpServerCard` + a real MCP server.
10. `apiCatalog` + `oauthProtectedResource` — if you have an authenticated API.
11. `webMcp` — if the site has interactive flows worth exposing as tools.
12. `authMd` + `a2aAgentCard` — delegated agent access.
13. Commerce protocols — pick by channel, not by count.

**Skip unless it applies**
`dnsAid` (you operate agent infrastructure), `webBotAuth` (you operate a
crawler), `ap2` (you already run A2A).

---

## Reasonable targets

| Site type | Sensible ceiling | Why |
|---|---|---|
| Blog, portfolio, brochure | **3** Agent-Readable | Nothing to call. Spend the rest of the effort on content quality and markdown. |
| Documentation, knowledge base | **4** Agent-Integrated | `agentSkills` + `ard` + `llms.txt` is exactly the shape docs want. |
| SaaS with a public API | **4–5** | `apiCatalog` + `oauthProtectedResource` + MCP server; level 5 when delegated access is a product. |
| E-commerce | **4** + one commerce protocol | Pick the channel you want to sell through. |
| Agent or MCP vendor | **5** | You are the use case. |
