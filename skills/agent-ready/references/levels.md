# The 0–5 ladder, and what to do at each rung

## The ladder

Each level requires everything below it. The rules are implemented in
`compute_level()` in `scripts/agent_ready_scan.py` and were derived from 20
reference reports spanning every level from 0 to 5 — see
`docs/METHODOLOGY.md` §2 for the derivation and the evidence pinning each rule.

| Level | Name | Requires |
|---|---|---|
| **0** | Not Ready | — no valid robots.txt, or no sitemap |
| **1** | Basic Web Presence | `robotsTxt` + `sitemap` |
| **2** | Bot-Aware | + `robotsTxtAiRules` + `contentSignals` |
| **3** | Agent-Readable | + `markdownNegotiation` |
| **4** | Agent-Integrated | + **any one** of `apiCatalog`, `mcpServerCard`, `a2aAgentCard`, `agentSkills` |
| **5** | Agent-Native | + `oauthDiscovery` |

**The ladder is sequential.** A check that would satisfy a higher rung does not
count until every lower rung is satisfied. `stripe.com` publishes an agent
skills index — which is a level-4 surface — and is still level 1, because it
declares no Content Signals.

Everything else — `linkHeaders`, `dnsAid`, `webBotAuth`,
`oauthProtectedResource`, `authMd`, `webMcp`, `ard`, every commerce check, the
whole extended track — is **outside the ladder** and never changes the level.
That does not make those checks unimportant; it makes the level a floor rather
than a score.

Two surprises worth internalising, both of which the data forces:

- **`authMd` is not a gate anywhere.** `workos.com` publishes one at level 1;
  `vercel.com` reaches level 5 without one.
- **`webMcp` and `ard` do not currently count toward level 4.** No observed
  site passes either as its *only* discovery surface, so their contribution
  could not be established and they are excluded conservatively. A site in that
  unusual position will be scored one level low here — run `--remote` if you
  think you are that site.

### Validation

`docs/verify/verify_ladder.py` replays these rules against 20 cached reference
reports: **20/20 levels reproduced**, covering levels 0, 1, 2, 3, 4 and 5.
`docs/verify/verify_parity.py` re-checks the whole scanner live. Run both after
any change to a check.

---

## What each rung actually buys you

**0 → 1 — be legible at all.** robots.txt and a sitemap. An agent that cannot
enumerate your pages treats your site as whatever it happened to land on. Half
an hour of work, and nothing downstream works without it.

**1 → 2 — state your terms.** Content Signals is the only place you get to say,
machine-readably, whether your content may be used for training, for grounding
generative answers, or only for classic search. Publishing nothing is not
neutrality — it leaves the decision entirely to the crawler. Note that passing
`robotsTxtAiRules` is not enough on its own; both checks gate this rung.

**2 → 3 — stop making agents read HTML.** Markdown negotiation is the highest
value-per-hour item on the whole ladder: no new endpoint, no new protocol, one
server rule, and every agent that touches the site suddenly reads far more of
the content within the same context budget. If a site does exactly one thing
from this document, this is the one.

**3 → 4 — give agents something to call.** One surface is enough, so pick the
one that matches what the site actually has:

| The site is… | Cheapest honest surface |
|---|---|
| documentation, a knowledge base, a blog with real procedural content | `agentSkills` — markdown files, no server |
| an existing REST/GraphQL API | `apiCatalog` — one linkset document |
| already running an MCP server | `mcpServerCard` — one JSON file |
| already running an agent others delegate to | `a2aAgentCard` |

Ship the card only when there is something real behind it. An MCP card pointing
at a dead endpoint, or an empty skills index, is worse than publishing nothing:
it wastes an agent's call and teaches it not to trust the domain.

**4 → 5 — let agents authenticate.** `oauthDiscovery` — publishing OAuth or
OIDC discovery metadata so an agent can move from reading the site to acting
within it as a user. This is a product decision, not a config change. A site
with no login has no honest path to level 5, and should not want one.

---

## Prioritising a real backlog

Sort by impact ÷ effort, not by ladder order — except that the level itself only
moves in ladder order.

**Tier 1 — hours, benefits every agent**
1. `robotsTxt` + `sitemap` + `contentSignals` — one file.
2. `markdownNegotiation` — one server rule.
3. `serverRendered`, `statusSanity`, `htmlSemantics` — if these fail, nothing
   above them matters, because the content an agent retrieves is empty or wrong.
4. `linkHeaders` — one header, and it reaches agents that never parse HTML.

**Tier 2 — a day, unlocks level 4**
5. One surface from the table above.
6. `structuredData` — Organization + WebSite JSON-LD.
7. `llmsTxt` — curated reading order.
8. `ard` (`ai-catalog.json`) — the index tying the surfaces together. Does not
   move the level on its own, but it is how registries find the rest.

**Tier 3 — a project, only with a reason**
9. `oauthDiscovery` + `oauthProtectedResource` — an authenticated API or MCP
   server.
10. `webMcp` — interactive flows worth exposing as callable tools.
11. `authMd` — delegated agent registration.
12. Commerce protocols — pick by sales channel, not by count.

**Skip unless it applies**
`dnsAid` (the site operates agent infrastructure), `webBotAuth` (it operates a
crawler), `ap2` (it already runs A2A).

---

## Reasonable targets

The right ceiling depends on what the site *is*. Pushing past it produces
files nobody calls.

| Site type | Sensible ceiling | Why |
|---|---|---|
| Blog, portfolio, brochure | **3** Agent-Readable | Nothing to call. Spend the remaining effort on content quality and the extended track. |
| Documentation, knowledge base | **4** Agent-Integrated | `agentSkills` is exactly the shape docs already have. |
| SaaS with a public API | **4–5** | `apiCatalog` gets you to 4; level 5 when delegated access is a product decision you have actually made. |
| E-commerce | **4** + one commerce protocol | Pick the channel you want to sell through. |
| Agent or MCP vendor | **5** | You are the use case. |

A level 3 site with a clean extended track serves agents better than a level 4
site whose homepage is an empty JavaScript shell. Report the level, then report
what actually matters.
