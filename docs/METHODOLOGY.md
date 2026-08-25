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

**Step 4 — derive the ladder.** This took two attempts, and the first one was
wrong in an instructive way.

*The wrong way.* `/api/scan` also returns a `nextLevel` object naming checks
that appear to block the next rung. Deriving the rules from four sites'
`nextLevel` lists produced a ladder that matched all four — and then failed on
the fifth site tried. The lists are **advisory**: a curated set of suggested
fixes, not the gate. The proof is `vercel.com`, which the reference places at
level 5 while it still fails `authMd` — yet `authMd` is listed as a
"requirement" for every level-4 site. Do not derive rules from that field.

*The right way.* Ignore `nextLevel` entirely. Collect the reference's own
per-check pass/fail results for a spread of sites, and solve for the smallest
rule set that reproduces every assigned level. Twenty sites were collected,
covering **every level from 0 to 5**:

| Level | Fixtures |
|---|---|
| 0 | `github.com` |
| 1 | `anthropic.com`, `hackmd.io`, `posthog.com`, `stripe.com`, `workos.com` |
| 2 | `sentry.io`, `www.baccan.it` |
| 3 | `cloudflare.com` |
| 4 | `agentskills.io`, `descope.com`, `developers.cloudflare.com`, `docs.stripe.com`, `isitagentready.com`, `modelcontextprotocol.io`, `netlify.com`, `railway.app`, `supabase.com` |
| 5 | `apify.com`, `vercel.com` |

The rules that fall out, implemented in `compute_level()`:

| Level | Name | Requires |
|---|---|---|
| 0 | Not Ready | — |
| 1 | Basic Web Presence | `robotsTxt` + `sitemap` |
| 2 | Bot-Aware | + `robotsTxtAiRules` + `contentSignals` |
| 3 | Agent-Readable | + `markdownNegotiation` |
| 4 | Agent-Integrated | + **any one** of `apiCatalog`, `mcpServerCard`, `a2aAgentCard`, `agentSkills` |
| 5 | Agent-Native | + `oauthDiscovery` |

The ladder is sequential: a check that would satisfy a higher rung does not
count until every lower rung is satisfied. `stripe.com` passes `agentSkills`
and is still level 1, because `contentSignals` blocks it at 1 → 2.

**The evidence that pins each rule:**

- **L1 is `robotsTxt` + `sitemap`, not more.** `anthropic.com`, `posthog.com`,
  `stripe.com` and `workos.com` all reach level 1 while failing `linkHeaders`,
  so `linkHeaders` is outside the ladder. (`github.com`'s advisory list names
  it — another reason not to trust that field.)
- **L2 needs both bot-control checks.** `stripe.com` passes
  `robotsTxtAiRules`, fails `contentSignals`, and stays at 1.
- **L4 is one surface, not two.** `docs.stripe.com` is level 4 passing
  `agentSkills` and nothing else in the group; `cloudflare.com` passes none of
  the four and stays at 3. That interval pins the threshold at exactly one.
- **L5 is `oauthDiscovery`.** Every one of the nine level-4 fixtures fails it;
  both level-5 fixtures pass it. It is the only check that separates them.
- **`authMd` is not a gate at all.** `workos.com` passes it at level 1;
  `vercel.com` reaches level 5 without it.

**Remaining uncertainty, stated honestly.** Two things this evidence cannot
settle:

1. Whether `webMcp` and `ard` also unlock level 4. No fixture passes either as
   its *only* discovery surface, so they are excluded conservatively — a site
   in that position would be scored one level low here.
2. Whether level 5 additionally requires `apiCatalog`. Both level-5 fixtures
   pass it, and no fixture passes `oauthDiscovery` while failing `apiCatalog`
   at level 4+, so the two cannot be separated with this data.

`docs/verify/verify_ladder.py` replays these rules against all 20 cached
reports and currently reproduces **20/20** levels. Run it after any change.

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
| 7 | `a2aAgentCard` also probes the pre-v0.3 path `/.well-known/agent.json`, and **warns** when the card is found only there | `cloudflare.com` publishes a real A2A card ("Cloudflare Site Agent", 2 skills) at the legacy path. The reference probes only `agent-card.json` and reports fail. Warning rather than passing keeps the level in agreement while still telling the site something true and actionable: agents following the current spec will not find that card. |

---

## 5. Validation

Two suites, testing different things. Neither asserts parity — both measure it.

### `verify_ladder.py` — are the rules right?

Replays `compute_level()` against the 20 cached reference reports in
`docs/verify/fixtures/reference-levels.json` and checks it reproduces the level
the reference assigned. Runs in milliseconds, is deterministic, and keeps
working when a fixture site changes.

```bash
python docs/verify/verify_ladder.py            # 20/20 on 2026-08-25
python docs/verify/verify_ladder.py --refresh  # re-fetch the fixtures first
```

This is the suite that pins the ladder. It covers every level from 0 to 5, and
it is what caught the first, wrong derivation described in §2.

### `verify_parity.py` — is the whole scanner right?

Scans a site both locally and through `/api/scan` and compares the assigned
level end to end — every check, not just the arithmetic.

```bash
python docs/verify/verify_parity.py
```

It deliberately does **not** fail on differing next-level lists, because the
reference's list is advisory (§2). Both lists are printed for information.

Result on 2026-08-25: level agreement on every site tested, across levels 0, 2,
3, 4 and 5. The one divergence found — `cloudflare.com` — turned out to be the
reference missing a real A2A card at a legacy path, and is resolved as
divergence 7 in §4.

**What this does and does not prove.** Twenty fixtures spanning all six levels
is enough to pin the rules and to catch a structural error. It is not enough to
settle the two residual questions in §2. Treat it as evidence, not a guarantee,
and re-run both suites when these drafts move.

---

## 6. Reproducing all of it

```bash
# a single scan, with the reference's answer alongside
python skills/agent-ready/scripts/agent_ready_scan.py example.com --remote -v

# re-derive the probe paths from the reference's evidence trail
python docs/verify/extract_probes.py

# are the ladder rules still right?  (fast, offline, 20 cached fixtures)
python docs/verify/verify_ladder.py

# is the whole scanner still right?  (slow, live)
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
- **Two ladder questions are unresolved** — whether `webMcp`/`ard` unlock
  level 4, and whether level 5 also needs `apiCatalog`. §2.
- **`isCommerce` is heuristic** — JSON-LD `Product`/`Offer`, cart and checkout
  routes, known platform fingerprints. A false negative silently turns five
  commerce checks from fail into n/a, which flatters the site.
- **Twenty fixtures**, but thinly spread at the ends: one site at level 0, one
  at level 3, two at level 5. A rule that only misbehaves at those rungs would
  be caught by a single fixture, or not at all.
