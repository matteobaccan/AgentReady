<img src="docs/assets/logo-wordmark.svg" alt="AgentReady" width="330">

A Claude Code skill that answers **"is this site ready for AI agents?"** — and
then fixes it.

It scores any URL 0–5 across 30 checks and generates the exact `robots.txt`,
`llms.txt`, `.well-known/*` files and server rules needed to move up. The 22
core checks and the level ladder reproduce
[isitagentready.com](https://isitagentready.com) (Cloudflare); 8 further checks
cover things that scanner does not score but agents depend on.

```
$ python skills/agent-ready/scripts/agent_ready_scan.py www.baccan.it

==============================================================================
Agent Readiness: https://www.baccan.it
Level 2/5 - Bot-Aware
==============================================================================

## Discoverability   (fail:1 neutral:1 pass:2)
  [PASS] robotsTxt                robots.txt exists with valid format
  [PASS] sitemap                  sitemap.xml exists with valid structure
  [FAIL] linkHeaders              No Link headers found on target page
  [n/a ] dnsAid                   Could not reliably determine DNS-AID support (SERVFAIL)
...
Next level -> 3 Agent-Readable, requires:
  * markdownNegotiation: Support Accept: text/markdown content negotiation
```

## Install

### As a plugin (recommended)

```
/plugin marketplace add matteobaccan/AgentReady
/plugin install agent-ready@agentready
```

### As a personal skill

```bash
# macOS / Linux
cp -r skills/agent-ready ~/.claude/skills/

# Windows PowerShell
Copy-Item -Recurse skills\agent-ready $env:USERPROFILE\.claude\skills\
```

Then just ask: *"is baccan.it agent-ready?"*, *"score this site for AI agents"*,
*"generate the .well-known files to get us to level 4"*.

## The scanner on its own

No dependencies beyond Python 3.8 stdlib. It works without Claude Code.

```bash
python skills/agent-ready/scripts/agent_ready_scan.py example.com \
    --markdown report.md --json report.json

# flags
--deep          also fetch same-origin scripts when looking for WebMCP
--remote        also run the official isitagentready.com scan and compare
--no-extended   only the 22 official checks
--only CATS     comma-separated categories to print
-v              per-check evidence: every URL probed and what came back
```

Exit code is 0 at level ≥ 1, 1 otherwise — usable as a CI gate.

## What it checks

| Category | Checks |
|---|---|
| **Discoverability** | `robotsTxt` `sitemap` `linkHeaders` `dnsAid` |
| **Content Accessibility** | `markdownNegotiation` |
| **Bot Access Control** | `robotsTxtAiRules` `contentSignals` `webBotAuth` |
| **API, Auth & MCP Discovery** | `apiCatalog` `oauthDiscovery` `oauthProtectedResource` `authMd` `mcpServerCard` `a2aAgentCard` `agentSkills` `webMcp` `ard` |
| **Commerce** | `x402` `mpp` `ucp` `acp` `ap2` |
| **Extended** (not scored in the ladder) | `llmsTxt` `structuredData` `htmlSemantics` `serverRendered` `transport` `statusSanity` `securityTxt` `feed` |

## The ladder

| Level | Name | Requires |
|---|---|---|
| 0 | Unprepared | — |
| 1 | Basic Web Presence | `robotsTxt` + `sitemap` |
| 2 | Bot-Aware | + `robotsTxtAiRules` + `contentSignals` |
| 3 | Agent-Readable | + `markdownNegotiation` |
| 4 | Agent-Integrated | + any two of `apiCatalog` `mcpServerCard` `agentSkills` `webMcp` `ard` `oauthDiscovery` |
| 5 | Agent-Native | + `authMd` + `a2aAgentCard` |

Verified to produce the same level *and* the same next-level requirements as
isitagentready.com on `stripe.com` (1), `www.baccan.it` (2),
`developers.cloudflare.com` (4) and `isitagentready.com` (4). Re-check any time
with `--remote`.

## Templates you can deploy

`skills/agent-ready/assets/` holds a fill-in-the-blanks version of every file a
site needs:

```
robots.txt                          AI bot rules + Content Signals + Sitemap + Agentmap
llms.txt                            curated entry point for LLMs
auth.md                             agent registration (WorkOS auth.md)
well-known/ai-catalog.json          ARD capability manifest
well-known/mcp.json                 MCP Server Card
well-known/agent-card.json          A2A Agent Card
well-known/api-catalog.json         RFC 9727 linkset
well-known/agent-skills/index.json  Agent Skills discovery index
well-known/security.txt             RFC 9116
snippets/serving-recipes.md         markdown negotiation + Link headers for
                                    Cloudflare, nginx, Apache, Express, Next.js
snippets/webmcp.js                  document.modelContext tool registration
snippets/head-and-jsonld.html       Organization/WebSite JSON-LD + discovery links
```

Every `{{PLACEHOLDER}}` must be replaced before deploying — a malformed file
fails the same check it was meant to pass.

## Standards covered

RFC 9309 (robots.txt) · RFC 8288 (Link) · RFC 7763 (text/markdown) ·
RFC 9727 (API Catalog) · RFC 8414 / RFC 9728 (OAuth discovery, protected
resources) · RFC 9421 (HTTP message signatures) · RFC 9116 (security.txt) ·
[Content Signals](https://contentsignals.org/) ·
[llms.txt](https://llmstxt.org/) ·
[MCP](https://modelcontextprotocol.io/) ·
[A2A](https://a2a-protocol.org/) ·
[ARD](https://agenticresourcediscovery.org/spec/) ·
[WebMCP](https://github.com/webmachinelearning/webmcp) ·
[DNS-AID](https://datatracker.ietf.org/doc/draft-mozleywilliams-dnsop-dnsaid/) ·
[auth.md](https://github.com/workos/auth.md) ·
x402 · MPP · UCP · ACP · AP2

## Documentation

| Document | What is in it |
|---|---|
| [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) | How the check list, probe paths and level ladder were recovered from the reference tool's public API; deliberate divergences; how to reproduce all of it |
| [`docs/SOURCES.md`](docs/SOURCES.md) | Every spec and endpoint relied on, each marked as read directly or cited from a search listing, with a link-check date |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Decisions already made and why; the ones still open, with recommendations |
| [`skills/agent-ready/references/checks.md`](skills/agent-ready/references/checks.md) | All 30 checks: probe, pass condition, fix, spec link |
| [`skills/agent-ready/references/levels.md`](skills/agent-ready/references/levels.md) | The ladder, its validation, a prioritised backlog |

## Verifying it yourself

```bash
python docs/verify/verify_parity.py    # does this agree with the reference? exit 0 if yes
python docs/verify/extract_probes.py   # re-derive the probe paths from the reference's evidence trail
```

Both are stdlib-only and hit the network. `verify_parity.py` is usable as a CI
gate: it fails if the level *or* the set of blocking checks diverges.

## Caveats

- **The level-4 rule is inferred, not observed.** "Any two of six" is
  consistent with every fixture tested but is not proven. It is the weakest
  claim here — see [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) §2, and use
  `--remote` when the answer has to be authoritative.
- **WebMCP** is detected by scanning HTML and (with `--deep`) same-origin
  scripts. The reference scanner loads the page in a real browser, so a fail
  here can be a false negative on a heavily bundled site.
- **DNS-AID** reports `n/a` rather than `fail` on `SERVFAIL` — absence of proof
  is not proof of absence.
- **The Agent Skills discovery index is a convention, not a ratified spec** —
  its `$schema` URL does not currently resolve. See
  [`docs/SOURCES.md`](docs/SOURCES.md) §3.
- Several of these specs are drafts (ARD v0.9, WebMCP, DNS-AID, auth.md,
  Content Signals). Paths and field names will move; the parity suite is how
  you find out that they have.

## Attribution

The 22 core checks and the 0–5 ladder reproduce the scoring model of
[isitagentready.com](https://isitagentready.com), a Cloudflare, Inc. product.
That model was recovered by observing the responses of its public `/api/scan`
endpoint, as documented in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

This repository contains no Cloudflare code, copy or assets. The remediation
guidance in `references/` and every template in `assets/` is original work
written against the primary specifications listed in
[`docs/SOURCES.md`](docs/SOURCES.md). It is not affiliated with or endorsed by
Cloudflare.

## License

MIT — see [`LICENSE`](LICENSE).
