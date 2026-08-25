# Decisions

Two kinds: choices already made while building this (recorded so they can be
revisited with the reasoning intact), and choices that are **yours** and are
still open.

Each open decision states what is at stake, the options, a recommendation, and
what changes downstream if you pick differently. None of them block using the
tool today.

---

# Part 1 — Already decided

| # | Decision | Rationale | Cost of reversing |
|---|---|---|---|
| D1 | **Reimplement locally rather than wrap `/api/scan`** | The skill works offline-ish, has no rate limit, no third-party dependency for normal use, and can add checks the reference does not have. `--remote` keeps the reference one flag away. | Low — the wrapper still exists as `--remote`. |
| D2 | **Python 3.8 stdlib only, no dependencies** | A skill that needs `pip install` fails the first time someone runs it on a clean machine. | Low. |
| D3 | **Extended checks are reported but excluded from the level** | Mixing them in would break parity with the reference and make the number incomparable. | Low — one flag in `compute_level()`. |
| D4 | **Repo name `AgentReady`** *(your call, 2026-08-25)* | Matches the local folder, the README install command, and existing plugin/marketplace ids. | Medium — renaming a public repo breaks `/plugin marketplace add` for anyone who already added it. |
| D5 | **MIT license** | Permissive, matches the ecosystem (ARD is Apache 2.0, Agent Skills is open). See open decision O2 if you want to reconsider. | Medium — you cannot un-MIT code others already took. |
| D6 | **Logo: 0–5 level meter** *(your call)* | The ladder *is* the product; the mark stays meaningful next to the level table and legible at 16px. | Trivial. |
| D7 | **No Claude attribution in commits** *(your call)* | You are the author of record. | Trivial. |

---

# Part 2 — Open decisions

## O1 · Publish the repo publicly?

**At stake:** whether this is a personal tool or a piece of ecosystem
infrastructure.

The honest framing: this reimplements the scoring model of a Cloudflare
product, recovered from its public API. That is legitimate — the API is public,
no Cloudflare code or copy is included, the remediation content is original, and
`docs/SOURCES.md` credits the reference prominently. But publishing makes that
relationship visible, so it should be a deliberate choice rather than a default.

| Option | Consequence |
|---|---|
| **Public on GitHub** *(recommended)* | Others can install it; the attribution in `SOURCES.md` does its job in the open; you own the `agent-ready` search term on GitHub. |
| Private | You keep the tool, nobody audits the level-4 inference, and the plugin install path in the README does not work for anyone else. |

**Recommendation: public.** The attribution is already written and accurate. If
you want a lighter touch, drop the plugin/marketplace manifests and publish it
as "a scanner and a set of templates" rather than "an isitagentready.com
reimplementation" — same code, different framing.

---

## O2 · Keep MIT, or move to Apache 2.0?

**At stake:** patent posture, and consistency with what this builds on.

MIT is the ecosystem default and is already in place. Apache 2.0 adds an
explicit patent grant and a `NOTICE` mechanism — relevant here only because
several protocols in scope (ARD, agentic commerce) come from large patent
holders and this repo encodes their formats in templates.

**Recommendation: keep MIT.** The patent surface of a scanner and some JSON
templates is essentially nil. Reconsider only if this grows into a library
other companies embed.

---

## O3 · The level-4 rule: keep the inference, or defer to the reference?

**This is the weakest claim in the repository** and you should know it is here.

Levels 1, 2, 3 and 5 are pinned by observed data. Level 4 — "any two of
`apiCatalog`, `mcpServerCard`, `agentSkills`, `webMcp`, `ard`,
`oauthDiscovery`" — is inferred from two sites that each pass four or five of
that pool. The observations are consistent with the rule but do not prove the
threshold is two, nor that the six count equally. Full reasoning in
`docs/METHODOLOGY.md` §2.

| Option | Consequence |
|---|---|
| **Keep it, documented as an approximation** *(recommended)* | Works offline, matches the reference on every fixture tested, and the caveat is written down in three places. |
| Make `--remote` the default | Authoritative levels always; but every scan then sends the target URL to a third party and takes 60–90s instead of ~10s. |
| Drop levels, report only per-check results | Honest, and much less useful — the single number is what makes a report actionable. |

**Recommendation: keep it.** Re-run `python docs/verify/verify_parity.py`
whenever the drafts move; that is what will tell you the rule has drifted.

---

## O4 · Add site-type profiles?

The reference offers *All checks* / *Content site* / *API-application*. This
scanner always runs everything and marks the inapplicable ones `n/a`.

| Option | Consequence |
|---|---|
| **Leave as is** *(recommended)* | `n/a` already communicates "not a gap for you", and a full scan surfaces things a narrow profile would hide. |
| Add `--profile content\|api\|commerce` | Shorter reports; risk of a site self-selecting out of a check it actually needed. |

**Recommendation: leave it.** Revisit if reports feel noisy in practice.

---

# Part 3 — Decisions about `www.baccan.it` itself

Current state: **level 2/5, Bot-Aware**. Hosted on **Netlify**
(`Server: Netlify`). `llms.txt` is already published and passing. `rss.xml`
exists but is not linked from `<head>`.

## O5 · What should `Content-Signal: ai-train=` say?

**The only decision here with consequences outside your website.** It is a
public, machine-readable statement of whether models may train on your writing.
Your `robots.txt` currently says:

```
Content-Signal: ai-train=no, search=yes, ai-input=yes
```

That is: *index me, ground your answers in me and cite me, but do not absorb me
into a model's weights.*

| Option | Who it fits |
|---|---|
| **`ai-train=no`** *(current, and my recommendation)* | Someone whose writing and talks are part of their professional identity. You get citation traffic without your corpus becoming an uncredited training set. |
| `ai-train=yes` | If your goal is for models to *know* your material by default, so they can answer about it without a retrieval step. Common for documentation whose success metric is being recalled correctly. |
| Omit the key | States no preference and leaves the decision entirely to the crawler. Not neutrality — abstention. |

**Recommendation: keep `ai-train=no`.** It matches a personal site whose value
is attribution. Note it is a preference with legal weight in some
jurisdictions, not an enforcement mechanism — crawlers can ignore it.

---

## O6 · Target level 3, or push to 4?

**Level 3** needs exactly one thing: `markdownNegotiation`.

**Level 4** additionally needs two of the discovery pool. For a personal site
the cheap pair is `agentSkills` + `ard` — both are static JSON/markdown files,
no server to run.

| Option | Effort | What you actually get |
|---|---|---|
| **Stop at 3** *(recommended)* | An afternoon | Every agent that reads your site gets ~5× more of your content per unit of context. This is the change that matters. |
| Push to 4 | A day, plus something real to publish | Only worth it if you have genuine procedural knowledge to expose as skills — your Java/Clipper/open-source material could qualify. Publishing an empty `ai-catalog.json` to score a point is theatre. |
| Push to 5 | A project | Requires `auth.md` and an A2A agent card, i.e. delegated credentialed access. Your site has no login. **Do not.** |

**Recommendation: 3 now, and 4 only if you want to publish real skills.**

---

## O7 · How to implement markdown negotiation on Netlify

Netlify `_redirects` cannot branch on the `Accept` header (only Country,
Language, Role), so this needs an Edge Function. The recipe is written and
ready in `skills/agent-ready/assets/snippets/serving-recipes.md` §1 → *Netlify*.

The real sub-decision is **where the markdown comes from**:

| Option | Consequence |
|---|---|
| **Generate `/md/**.md` twins at build time from the same source as the HTML** *(recommended)* | Always in sync. If your pages already originate in markdown, this is a copy step. |
| Convert HTML → markdown at the edge, on the fly | No build change, but you ship whatever your HTML happens to contain — nav, footers, cookie text. |
| Skip negotiation, publish `.md` twins and link them with `<link rel="alternate" type="text/markdown">` | Scores **warn**, not pass. Fine as a first step; agents that only do content negotiation will miss them. |

**A twin that drifts from the page is worse than no twin** — an agent will
quote the stale one confidently.

---

## O8 · The three free wins — do them regardless

Not really decisions; they cost minutes and are outside the ladder, so they
never show up as a level bump.

1. **`Link` headers** — one block in Netlify's `_headers`. Reaches agents that
   fetch your JSON or PDFs and never parse HTML. Recipe in `serving-recipes.md` §2.
2. **Link `rss.xml` from `<head>`** — the feed already exists. One `<link>` tag
   turns it from invisible into the cheapest change-notification channel an
   agent can use.
3. **`/.well-known/security.txt`** — one file, RFC 9116. Template in
   `assets/well-known/security.txt`.

Two more worth a look, from the extended track: the homepage is missing
`<main>`/`<article>` landmarks and OpenGraph tags. Neither is urgent; both are
cheap.

---

# Summary — what I would actually do

| Priority | Action | Effort |
|---|---|---|
| 1 | Markdown negotiation via Netlify Edge Function, markdown twins generated at build → **level 3** | afternoon |
| 2 | `Link` headers + `<link>` the RSS feed + `security.txt` | minutes |
| 3 | Keep `ai-train=no` | done |
| 4 | Publish the repo public, MIT, as is | minutes |
| 5 | Level 4 *only* if you have real skills to publish | a day |
| — | Level 5, commerce protocols, DNS-AID, Web Bot Auth | not applicable to this site |
