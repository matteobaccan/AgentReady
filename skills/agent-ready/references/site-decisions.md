# Decisions that belong to the site owner

Four questions come up in almost every audit. None of them has a technically
correct answer — each encodes a policy or product choice. **Raise them, give a
recommendation with the trade-off attached, and let the owner decide.** Picking
a default quietly is the failure mode here: these end up in public,
machine-readable files that state a position on the owner's behalf.

Present them when they become relevant, not as an upfront questionnaire.

---

## 1. What should `Content-Signal: ai-train=` say?

**The only decision here with consequences beyond the site.** It is a public,
machine-readable statement about whether models may train on this content.

| Value | Fits a site whose… |
|---|---|
| `ai-train=no` | writing *is* the asset, or the brand: attribution matters more than absorption. Personal sites, publishers, consultancies, anyone selling expertise. Common pairing: `search=yes, ai-input=yes, ai-train=no` — *index me, ground answers in me and cite me, but do not absorb me into weights.* |
| `ai-train=yes` | success metric is models **knowing** the material by default, so they answer correctly without a retrieval step. Documentation, SDKs, open standards, developer tooling. |
| key omitted | — |

Omitting the key is not neutrality. It states no preference and leaves the
decision entirely to the crawler. If an owner wants to abstain deliberately,
say so in the audit rather than letting silence look like an oversight.

Say this out loud when recommending: **signals are a stated preference, not an
enforcement mechanism.** They carry legal weight in some jurisdictions and are
ignored by some crawlers. A site that needs enforcement needs blocking, not
signalling.

Same applies to `ai-input`: saying `no` there removes the site from RAG-grounded
answers, which for most sites means removing themselves from the surface where
they would have been cited.

---

## 2. Which level should this site target?

Do not assume higher is better. Ask what the site is, then aim at the ceiling
from the table in `levels.md` and stop.

The test for going past level 3 is a single question: **is there anything here
worth an agent calling?** If the answer is "we would have to invent something",
the answer is no, and the effort belongs in the extended track instead —
`serverRendered`, `statusSanity`, `structuredData`, `llmsTxt`.

Publishing an empty `agent-skills/index.json` or an MCP card pointing at nothing
buys a level and costs credibility. An agent that calls a dead surface learns
not to trust the domain.

Level 5 is a product decision, not a configuration change: it means opening
authenticated access for agents acting as users. A site with no login has no
honest route there.

---

## 3. Where does the markdown come from?

Once `markdownNegotiation` is on the table, the real question is the source of
the markdown, not the server rule.

| Approach | Trade-off |
|---|---|
| **Generate `.md` twins at build time from the same source as the HTML** | Always in sync. Near-free if the site already originates in markdown. The default recommendation. |
| Convert HTML → markdown at the edge (Cloudflare's toggle, a Worker) | No build change, but ships whatever the HTML contains — navigation, footers, cookie banners — unless the converter strips them. |
| Publish `.md` twins and link them with `<link rel="alternate" type="text/markdown">`, no negotiation | Scores **warn**, not pass. A reasonable first step on a static host that cannot negotiate. |

State the failure mode plainly: **a markdown twin that drifts from the page is
worse than no twin at all.** An agent will quote the stale version confidently,
and nothing in the response tells it the page has moved on.

---

## 4. Which commerce protocol — if any?

Only relevant when the site is transactional. The checks report `n/a`
otherwise, and that is not a gap.

| Want to sell through… | Protocol |
|---|---|
| ChatGPT / Instant Checkout | ACP |
| Google's shopping surfaces | UCP |
| API calls or compute, priced per request | x402 (crypto-native) or MPP (payment-method agnostic) |
| an agent you already run over A2A | AP2 |

Choosing all of them is a sign of not having chosen. Each is an integration with
a counterparty, not a file to drop in `.well-known`. Ask which channel the
business actually wants, and implement that one.

---

## How to raise these in an audit

Put them after the findings, not before. Something like:

> Three of these depend on a decision that is yours rather than mine — I have
> flagged them rather than picking a default:
>
> - **`ai-train`**: your robots.txt currently says X. Given that this site is
>   *[what it is]*, I would keep/change it because *[reason]* — but it is a
>   public statement about your content, so tell me.
> - **Target level**: level N is a reasonable ceiling for this site. Going
>   further needs *[the specific thing you would have to build]*.
> - **Markdown source**: build-time twins or edge conversion — depends on
>   whether your pages already originate in markdown.

One recommendation each, the trade-off in a clause, and then stop. Do not
present a decision matrix for a personal blog.
