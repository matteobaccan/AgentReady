# Methodology

How the check list, the probe paths and the level ladder in this repository
were derived, what was verified, and where the implementation knowingly differs
from its reference.

Written so the work is auditable: every claim below can be re-run.

---

## 1. The problem

The brief was "make a Claude Code skill that does what
`isitagentready.com/www.baccan.it` does". That page renders a report but
publishes no rubric: no weights, no thresholds, no list of the paths it probes.
Reimplementing from the rendered HTML alone would have produced a plausible
guess, not a faithful one.

So the rubric was recovered from the tool's own behaviour rather than invented.

---

## 2. Recovering the rubric

**Step 1 — find the machinery.** The homepage is an Astro app. Its inline
bundle exposes a `scan_site` tool registered through WebMCP, whose own
description states the shape of the answer:

> "Returns a readiness level (0-5), results for all checks across 5 categories
> (discoverability, content, bot access control, discovery, commerce)"

and it calls `POST /api/scan` with `{"url": "..."}`. That endpoint is public.

**Step 2 — read a real report.** Calling it returns not just verdicts but a
full `evidence` array per check: each HTTP request made, with method, URL,
headers, response status and a body preview. That is the rubric, in machine
form.

```bash
curl -s -X POST https://isitagentready.com/api/scan \
     -H 'Content-Type: application/json' \
     -d '{"url":"https://www.baccan.it"}'
```

**Step 3 — extract every probe.** Scanning four sites and de-duplicating the
`evidence[].request.url` values yields the exact path list per check. This is
where the non-obvious paths came from — nothing in the ACP or UCP specs told us
the scanner looks at `/.well-known/acp.json` and `/.well-known/ucp`; its own
evidence did.

Reproduce it:

```bash
python docs/verify/extract_probes.py   # see §6
```

**Step 4 — derive the ladder.** `/api/scan` returns `level`, `levelName` and a
`nextLevel` object naming the specific checks that block the next rung. Four
sites at three different levels give enough simultaneous constraints to solve
for the rules:

| Site | Level | Blocking checks reported |
|---|---|---|
| `stripe.com` | 1 Basic Web Presence | `contentSignals` |
| `www.baccan.it` | 2 Bot-Aware | `markdownNegotiation` |
| `developers.cloudflare.com` | 4 Agent-Integrated | `authMd`, `a2aAgentCard` |
| `isitagentready.com` | 4 Agent-Integrated | `authMd`, `a2aAgentCard` |

Note what `stripe.com` proves: it passes `robotsTxtAiRules` but fails
`contentSignals`, and is blocked at 1 → 2 by `contentSignals` **alone**. So
level 2 needs both, and `robotsTxtAiRules` is not sufficient on its own.
And `www.baccan.it` fails `linkHeaders` yet is blocked at 2 → 3 only by
`markdownNegotiation` — so `linkHeaders` is outside the ladder entirely.

The resulting rules are in `compute_level()`:

| Level | Name | Requires |
|---|---|---|
| 0 | Unprepared | — |
| 1 | Basic Web Presence | `robotsTxt` + `sitemap` |
| 2 | Bot-Aware | + `robotsTxtAiRules` + `contentSignals` |
| 3 | Agent-Readable | + `markdownNegotiation` |
| 4 | Agent-Integrated | + any **two** of `apiCatalog`, `mcpServerCard`, `agentSkills`, `webMcp`, `ard`, `oauthDiscovery` |
| 5 | Agent-Native | + `authMd` + `a2aAgentCard` |

**Confidence, stated honestly.** Levels 1, 2, 3 and 5 are pinned by the
observed data. The level-4 rule — "any two of six" — is the weakest inference
in this repository. Both level-4 sites pass four or five of that pool, so the
observations are consistent with the rule but do not prove the threshold is
exactly two, nor that all six members count equally. It is a documented
approximation. If it matters to you, `--remote` gives the authoritative answer.

---

## 3. Writing the checks against primary specs

Probe paths came from the reference scanner. **Pass conditions and remediation
did not** — those were written against the primary specifications in
`SOURCES.md`, because a scanner tells you *whether* something is there, not what
correct looks like.

This is where the implementation adds value over a black-box reimplementation.
Three examples:

- **`markdownNegotiation`** — the reference reports pass/fail. RFC 7763 plus
  the content-negotiation literature says markdown served without `Vary: Accept`
  will be mis-cached by any CDN in front of it. So this repo returns **warn**
  in that case, with an explanation. Stricter than the reference, deliberately.
- **`ard`** — the full `ai-catalog.json` schema in `assets/` (the `urn:air:`
  identifier grammar, the `url`-xor-`data` rule, `representativeQueries`) came
  from reading the ARD spec, not from any scan.
- **`robotsTxtAiRules`** — the reference passes a bare wildcard group. Correct,
  and this repo matches it. But the spec's group-matching rule means adding a
  named `User-agent: GPTBot` group silently *removes* GPTBot from your wildcard
  `Content-Signal`. That trap is documented in `references/checks.md`; no
  scanner surfaces it.

---

## 4. Deliberate divergences from the reference

| # | Divergence | Why |
|---|---|---|
| 1 | **Soft-404 detection** on `authMd` and `llmsTxt` | A site with markdown negotiation answers `GET /anything.md` with the homepage. The reference scored `isitagentready.com`'s own `/auth.md` as fail; a naive reimplementation scored it **pass**, because the request really does return HTTP 200 with 2954 bytes of valid markdown. This repo compares the body against the homepage's markdown rendering and rejects the match. Found by comparing the two scanners' output, not by reading a spec. |
| 2 | `markdownNegotiation` returns **warn** without `Vary: Accept`, and **warn** for an explicit `.md` route with no negotiation | See §3. |
| 3 | `dnsAid` returns **n/a**, not fail, on `SERVFAIL` | Absence of proof is not proof of absence. The reference does the same; this repo makes the reasoning explicit in the message. |
| 4 | `webMcp` is a static scan; `--deep` also fetches up to 12 same-origin `<script src>` bundles | The reference loads the page in a real browser. This is the one check where a **fail can be a false negative**, and it is labelled as such in the output text itself. |
| 5 | An **extended track** of 8 checks | Things agents depend on that the reference does not score. Reported separately and excluded from the level, so parity is never compromised. |
| 6 | A live MCP endpoint with no server card scores **warn** | It works, but only for agents that already know the URL — which defeats discovery. |

---

## 5. Validation

Parity is not asserted, it is tested. Run:

```bash
python docs/verify/verify_parity.py
```

It scans each fixture locally and through `/api/scan`, and compares both the
level and the set of blocking checks.

Result on 2026-08-25 — **4/4 exact match on level and on next-level
requirements**:

| Site | This scanner | Reference | Match |
|---|---|---|---|
| `stripe.com` | 1 Basic Web Presence · needs `contentSignals` | 1 Basic Web Presence · needs `contentSignals` | ✅ |
| `www.baccan.it` | 2 Bot-Aware · needs `markdownNegotiation` | 2 Bot-Aware · needs `markdownNegotiation` | ✅ |
| `developers.cloudflare.com` | 4 Agent-Integrated · needs `authMd`, `a2aAgentCard` | same | ✅ |
| `isitagentready.com` | 4 Agent-Integrated · needs `authMd`, `a2aAgentCard` | same | ✅ |

Four fixtures across three levels is enough to catch a structural error in the
ladder. It is **not** enough to prove the level-4 threshold (§2). Treat parity
as evidence, not as a guarantee, and re-run it when these drafts move.

---

## 6. Reproducing all of it

```bash
# a single scan, with the reference's answer alongside
python skills/agent-ready/scripts/agent_ready_scan.py example.com --remote -v

# re-derive the probe paths from the reference's evidence trail
python docs/verify/extract_probes.py

# re-run the parity suite
python docs/verify/verify_parity.py
```

No dependencies beyond the Python 3.8 standard library. Both verify scripts hit
the network and take a couple of minutes; `/api/scan` can take 60–90s per site.

---

## 7. Known limitations

- **Drafts move.** ARD is v0.9. WebMCP's API surface moved from `navigator` to
  `document` in May 2026. DNS-AID, auth.md and Content Signals are all
  Internet-Drafts. Paths and field names in `assets/` will need revisiting; the
  parity suite is how you find out that they have.
- **The Agent Skills discovery index is a convention, not a spec.** Its
  `$schema` URL does not resolve. See `SOURCES.md` §3.
- **No JavaScript execution.** `webMcp` and `serverRendered` both judge a page
  from its initial HTML. That is the right lens for most crawling agents, and
  the wrong one for a browser-driving agent.
- **The level-4 rule is inferred**, not observed. §2.
- **`isCommerce` is heuristic** — JSON-LD `Product`/`Offer`, cart and checkout
  routes, known platform fingerprints. A false negative silently turns five
  commerce checks from fail into n/a, which flatters the site.
- **Four fixtures.** No site at level 0, 3 or 5 was available to test against.
