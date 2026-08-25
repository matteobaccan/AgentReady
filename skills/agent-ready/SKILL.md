---
name: agent-ready
description: Audit and fix how ready a website is for AI agents - robots.txt, Content Signals, markdown negotiation, llms.txt, MCP server cards, agent skills, ARD/ai-catalog.json, WebMCP, OAuth discovery, auth.md, A2A cards and agentic commerce. Use when asked whether a site is agent-ready, AI-ready or LLM-ready, to score it 0-5, to fix a failing check, or to generate the .well-known files a site needs for agents.
---

# Agent readiness: audit and fix

Scores a site 0–5 on the standards AI agents use to find, read and act on it,
then generates the exact files needed to move it up. Reproduces the 22 checks
Cloudflare's isitagentready.com runs, plus 8 extended checks it does not.

## Decide what the user is asking for

| Ask | Do |
|---|---|
| "is my site agent-ready / AI-ready", a bare URL, "score my site" | **Audit** |
| "fix X", "make it level 4", "generate the files" | **Fix** — audit first if you have not |
| "what is llms.txt / ARD / Content Signals", "should I …" | Answer from `references/checks.md`; do not scan |
| "review my robots.txt / ai-catalog.json" (file in the repo) | Read the file, validate against `references/checks.md` |

---

## Audit

Run the scanner. It is stdlib-only Python 3.8+, no install step.

```bash
python skills/agent-ready/scripts/agent_ready_scan.py <url> \
  --markdown agent-readiness.md --json agent-readiness.json
```

Useful flags:

- `--deep` — also fetch same-origin scripts when looking for WebMCP. Use it
  before telling someone their WebMCP is missing.
- `--remote` — additionally run the official isitagentready.com scan and print
  both levels. Use it when the user disputes a result, or to confirm parity.
- `--no-extended` — only the 22 official checks.
- `-v` — per-check evidence (every URL probed and what came back).
- `--only discoverability,discovery` — narrow the printed report.

The scanner never raises: unreachable hosts and crashed checks come back as
`err` rows.

### Reporting the result

Lead with the level and the single next thing. Then the fails grouped by
category, then the extended track. Keep it short — the JSON has the detail.

State the level as a floor, not a grade: level 2 with a strong extended track
is a better site for agents than level 4 with an empty homepage. When a check
is **n/a**, say so rather than counting it as a failure — `dnsAid`, `webBotAuth`
and the commerce checks are not gaps for most sites.

Do not offer to fix things the user has not asked about yet. Give the level, the
next rung, and stop.

---

## Fix

Read `references/levels.md` before proposing an order of work. The ladder only
moves in sequence, but effort should be spent by impact.

For each check to fix:

1. Read its entry in `references/checks.md` — probe, pass condition, trap.
2. Copy the matching template from `assets/`, replace every `{{PLACEHOLDER}}`
   with real values from the site. **Never ship a file with a placeholder left
   in it** — a malformed `ai-catalog.json` fails the same check it was meant
   to pass.
3. Put it where the site actually serves static files. Find that out; do not
   assume a docroot.
4. Set the content type. `references/checks.md` and
   `assets/snippets/serving-recipes.md` §3 list every one — this is the most
   common way a correct file still fails.
5. Re-run the scanner against the deployed URL. A file in the repo proves
   nothing.

### What is in `assets/`

| File | Fixes |
|---|---|
| `robots.txt` | `robotsTxt`, `robotsTxtAiRules`, `contentSignals`, `sitemap` reference, ARD `Agentmap` |
| `llms.txt` | `llmsTxt` |
| `auth.md` | `authMd` |
| `well-known/ai-catalog.json` | `ard` |
| `well-known/mcp.json` | `mcpServerCard` |
| `well-known/agent-card.json` | `a2aAgentCard` |
| `well-known/api-catalog.json` | `apiCatalog` (serve at `/.well-known/api-catalog`, no extension) |
| `well-known/agent-skills/index.json` | `agentSkills` |
| `well-known/security.txt` | `securityTxt` |
| `snippets/serving-recipes.md` | `markdownNegotiation`, `linkHeaders`, content types |
| `snippets/webmcp.js` | `webMcp` |
| `snippets/head-and-jsonld.html` | `structuredData`, `htmlSemantics` |

### Judgement calls to raise, not decide

Four questions in every audit encode a policy or product choice the site owner
owns: the `ai-train` Content Signal, which level to target, where the markdown
comes from, and which commerce protocol (if any). **Read
`references/site-decisions.md` before raising any of them** — it has the
trade-offs, the recommendation for each site type, and how to present them
without turning a personal blog into a decision matrix.

Never pick a default quietly on these. They end up in public,
machine-readable files that state a position on the owner's behalf.

---

## Things that are true and easy to get wrong

- **Markdown negotiation without `Vary: Accept` is a bug**, not a partial win.
  A CDN will cache one representation and serve it to the wrong client.
- **A named `User-agent:` group replaces the wildcard group**, it does not add
  to it. Adding `User-agent: GPTBot` with one `Disallow` silently drops your
  `Content-Signal` for GPTBot.
- **`/.well-known/api-catalog` has no file extension** and must be
  `application/linkset+json`.
- **A site that markdown-negotiates every path returns 200 for
  `/anything.md`.** The scanner detects this soft-404 pattern; a hand check
  with `curl` will not.
- **`llms.txt` has no search-engine weight.** Google ignores it. Its value is
  curation for agents that choose to read it — publish it for that reason or
  not at all.
- **An MCP server card pointing at a dead endpoint is worse than no card.**
- **If `serverRendered` fails, fix that first.** Most crawling agents never run
  your JavaScript, so every check above it is scoring an empty page.

## References

- `references/checks.md` — all 30 checks: probe, pass condition, fix, spec link.
- `references/levels.md` — the ladder, its validation, a prioritised backlog,
  and the sensible ceiling per site type.
- `references/site-decisions.md` — the four owner decisions and how to raise them.
