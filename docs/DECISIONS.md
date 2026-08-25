# Decisions

Decisions about **this project**. Decisions about a *site being audited* are a
different thing and live in
[`skills/agent-ready/references/site-decisions.md`](../skills/agent-ready/references/site-decisions.md)
— the skill raises those with the site owner, one audit at a time.

---

## Part 1 — Settled

| # | Decision | Rationale | Cost of reversing |
|---|---|---|---|
| D1 | **Reimplement locally rather than wrap `/api/scan`** | Works without a third party, no rate limit, and can add checks the reference does not have. `--remote` keeps the reference one flag away. | Low — the wrapper still exists as `--remote`. |
| D2 | **Python 3.8 stdlib only, no dependencies** | A skill that needs `pip install` fails the first time someone runs it on a clean machine. | Low. |
| D3 | **Extended checks are reported but excluded from the level** | Mixing them in would break comparability with the reference and make the number mean something different from what everyone else's number means. | Low. |
| D4 | **Repo name `AgentReady`** | Matches the plugin and marketplace ids already in the manifests. | Medium — renaming a public repo breaks `/plugin marketplace add` for anyone who already added it. |
| D5 | **MIT licence** | Permissive, matches the surrounding ecosystem. | Medium — you cannot un-MIT code others already took. |
| D6 | **Logo: 0–5 level meter** | The ladder *is* the product; the mark stays meaningful next to the level table and legible at 16px. | Trivial. |
| D7 | **No Claude attribution in commits** | The repo owner is the author of record. | Trivial. |
| D8 | **Level rules derived from per-check results, not from `nextLevel`** | The reference's `nextLevel.requirements` is an advisory fix list, not the gate — `vercel.com` is level 5 while failing `authMd`, which that field lists as a requirement for every level-4 site. Deriving from it produced a ladder that matched four fixtures and broke on the fifth. See `METHODOLOGY.md` §2. | Low, but redoing it means re-collecting fixtures. |
| D9 | **`a2aAgentCard` warns, rather than passes, on the legacy `/.well-known/agent.json` path** | `cloudflare.com` publishes a real card there. Passing it would diverge from the reference's level; ignoring it would hide something true. Warning does both jobs: the level agrees, and the site learns its card is where current-spec agents will not look. | Trivial. |

### D10 · The level-4 and level-5 rules *(resolved — was the open question O3)*

The first derivation guessed "any two of six" for level 4 and
"`authMd` + `a2aAgentCard`" for level 5. **Both were wrong.** They matched the
four fixtures they were built from and failed immediately on wider testing.

Rather than pick between "keep the guess" and "always defer to `--remote`", the
uncertainty was removed: 20 reference reports were collected spanning every
level from 0 to 5, and the rules were solved from the reference's own per-check
results.

| Level | Requires |
|---|---|
| 4 | **any one** of `apiCatalog`, `mcpServerCard`, `a2aAgentCard`, `agentSkills` |
| 5 | `oauthDiscovery` |

Pinned by `docs/verify/verify_ladder.py` — **20/20 levels reproduced**. The
evidence for each rule is in `METHODOLOGY.md` §2.

**What is still unresolved,** and cannot be settled with the available
evidence:

1. Whether `webMcp` and `ard` also unlock level 4. No fixture passes either as
   its only discovery surface. Excluded conservatively, so a site in that
   position scores one level low here.
2. Whether level 5 additionally requires `apiCatalog`. Both level-5 fixtures
   pass it, and nothing separates the two conditions in this data.

Resolving either needs a fixture that does not currently exist in the wild —
or the reference publishing its rubric. Until then, `--remote` is the
tiebreaker.

---

## Part 2 — Open

*O1 is settled and kept here for its reasoning.*

### ~~O1 · Publish the repo publicly?~~ — *done*

Published at <https://github.com/matteobaccan/AgentReady>, MIT, public.

It was worth being deliberate about, because this reimplements the scoring
model of a Cloudflare product recovered from its public API. That is legitimate
— the API is public, no Cloudflare code or copy is included, and the
remediation content is original — but publishing makes the relationship
visible, so the attribution in `README.md` and `SOURCES.md` is doing real work
now rather than sitting there as boilerplate.

The three URL references (`homepage` in `.claude-plugin/plugin.json`, the
install commands in `README.md`, the `UA` string in `agent_ready_scan.py`) all
point at the live repo.

### O2 · Keep MIT, or move to Apache 2.0?

Apache 2.0 adds an explicit patent grant, relevant only because several
protocols in scope come from large patent holders and this repo encodes their
formats in templates.

**Recommendation: keep MIT.** The patent surface of a scanner and some JSON
templates is essentially nil. Reconsider if this becomes a library other
companies embed.

### O3 · Add site-type profiles?

The reference offers *All checks* / *Content site* / *API-application*. This
scanner always runs everything and marks the inapplicable ones `n/a`.

**Recommendation: leave as is.** `n/a` already communicates "not a gap for
you", and a full scan surfaces things a narrow profile would hide. Revisit if
reports feel noisy in practice.

### O4 · How often to re-run the fixtures?

Every spec in scope is a draft. ARD is v0.9; WebMCP moved its API surface from
`navigator` to `document` in May 2026; DNS-AID, auth.md and Content Signals are
Internet-Drafts. The reference will also change its own rules.

Options: run `verify_ladder.py` (fast, offline) on every commit via CI and
`verify_parity.py` (slow, live) on a schedule; or run both manually when
something looks wrong.

**Recommendation: CI on `verify_ladder.py`, monthly on `verify_parity.py`.**
The ladder test is free and catches the class of error that actually happened
here. Not yet set up — no CI configuration is committed.
