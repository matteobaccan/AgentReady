# Sources

Every specification, document and endpoint this project relies on. All URLs
were checked with an HTTP request on **2026-08-25**; the status column records
what came back.

The **Read** column is deliberate. `direct` means the content of that URL was
fetched and read while building this project. `listing` means the URL came from
a search-result summary and only its reachability was verified — the claims
attributed to it are second-hand and should be confirmed against the primary
document before you depend on them.

---

## 1. The reference implementation

This project reproduces the scoring model of Cloudflare's public scanner. That
scanner is the reference; where the two disagree, it wins, and
`--remote` exists to make the disagreement visible.

| Source | Status | Read | Used for |
|---|---|---|---|
| <https://isitagentready.com/> | 200 | direct | Category names, site-type filter, disclaimer |
| <https://isitagentready.com/www.baccan.it> | 200 | direct | The report layout the user pointed at |
| `POST https://isitagentready.com/api/scan` | 200 | direct | **The check list, level names, per-check evidence and probe URLs.** See `METHODOLOGY.md` §2 |
| <https://isitagentready.com/llms.txt> | 200 | direct | Cross-check of the 22 checks and their category grouping |
| <https://isitagentready.com/robots.txt> | 200 | direct | Content-Signal syntax in the wild |
| <https://isitagentready.com/.well-known/mcp.json> | 200 | direct | Real-world MCP server card shape |
| <https://isitagentready.com/.well-known/agent-skills/index.json> | 200 | direct | Real-world Agent Skills index shape |
| <https://blog.cloudflare.com/agent-readiness/> | 200 | listing | Announcement of the readiness score |

**Attribution.** isitagentready.com is a Cloudflare, Inc. product. This
repository is an independent reimplementation built by observing its public
API's responses. It ships no Cloudflare code, copy or assets. The remediation
text in `references/` and `assets/` is original, written against the primary
specifications listed below.

---

## 2. Core web standards (IETF / W3C)

| Spec | Status | Read | Check it backs |
|---|---|---|---|
| [RFC 9309 — Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309.html) | 200 | listing | `robotsTxt`, `robotsTxtAiRules` |
| [RFC 8288 — Web Linking](https://www.rfc-editor.org/rfc/rfc8288.html) | 200 | listing | `linkHeaders` |
| [RFC 7763 — `text/markdown`](https://www.rfc-editor.org/rfc/rfc7763.html) | 200 | listing | `markdownNegotiation` |
| [RFC 8615 — Well-Known URIs](https://www.rfc-editor.org/rfc/rfc8615.html) | 200 | listing | Every `/.well-known/*` path |
| [RFC 9727 — API Catalog](https://www.rfc-editor.org/rfc/rfc9727.html) | 200 | listing | `apiCatalog` |
| [RFC 8414 — OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414.html) | 200 | listing | `oauthDiscovery` |
| [RFC 9728 — OAuth 2.0 Protected Resource Metadata](https://www.rfc-editor.org/rfc/rfc9728.html) | 200 | listing | `oauthProtectedResource` |
| [RFC 9421 — HTTP Message Signatures](https://www.rfc-editor.org/rfc/rfc9421.html) | 200 | listing | `webBotAuth` |
| [RFC 9116 — security.txt](https://www.rfc-editor.org/rfc/rfc9116.html) | 200 | listing | `securityTxt` |
| [RFC 9460 — SVCB / HTTPS RRs](https://www.rfc-editor.org/rfc/rfc9460.html) | 200 | listing | `dnsAid` record types |
| [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html) | 200 | listing | `oauthDiscovery` fallback path |
| [sitemaps.org protocol](https://www.sitemaps.org/protocol.html) | 200 | listing | `sitemap` |
| [schema.org](https://schema.org/) · [validator](https://validator.schema.org/) | 200 | listing | `structuredData` |

---

## 3. AI-agent specifications

### Content Signals
| Source | Status | Read |
|---|---|---|
| <https://contentsignals.org/> | 200 | listing |
| [draft-romm-aipref-contentsignals](https://datatracker.ietf.org/doc/draft-romm-aipref-contentsignals/) | 200 | listing |
| [Cloudflare managed robots.txt](https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/) | 200 | listing |

Three signals: `search`, `ai-input` (RAG grounding), `ai-train`. Values `yes` /
`no`; an omitted key states no preference. Cloudflare's managed default is
`search=yes, ai-train=no` and deliberately leaves `ai-input` unset. Signals are
a stated preference, not an enforcement mechanism.

### Markdown content negotiation
| Source | Status | Read |
|---|---|---|
| [Cloudflare — Markdown for Agents](https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/) | 200 | listing |
| [acceptmarkdown.com — the `Accept: text/markdown` convention](https://acceptmarkdown.com/guides/accept-text-markdown) | 200 | listing |

Source of the `Vary: Accept` requirement, and of the reported ~80% token
reduction of markdown versus equivalent HTML (Cloudflare's figure — this
project has not independently measured it).

### llms.txt
| Source | Status | Read |
|---|---|---|
| <https://llmstxt.org/> | 200 | listing |

Late draft. No search-engine weight — Google does not use it. Its value is
curation for agents that choose to read it.

### DNS for AI Discovery
| Source | Status | Read |
|---|---|---|
| [draft-mozleywilliams-dnsop-dnsaid](https://datatracker.ietf.org/doc/draft-mozleywilliams-dnsop-dnsaid/) | 200 | listing |
| [Agent Identity & Discovery (AID) specification](https://aid.agentcommunity.org/docs/specification) | 200 | listing |

Two overlapping conventions, both probed by `dnsAid`: DNS-AID's
`_index|_a2a|_mcp._agents.<domain>` (SVCB/HTTPS/TXT), and AID's
`_agent.<domain>` TXT record. Layered on existing RR types; DNSSEC-signed
records are what make them trustworthy.

### Web Bot Auth
| Source | Status | Read |
|---|---|---|
| [draft-meunier-web-bot-auth-architecture](https://datatracker.ietf.org/doc/draft-meunier-web-bot-auth-architecture/) | 200 | listing |

Directory published at `/.well-known/http-message-signatures-directory`.

### Model Context Protocol
| Source | Status | Read |
|---|---|---|
| <https://modelcontextprotocol.io/> | 200 | listing |
| [SEP-2127 — MCP Server Cards, HTTP discovery via .well-known](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2127) | 200 | listing |

SEP-2127 is a working-group draft that supersedes the earlier SEP-1649. Card
path is `/.well-known/mcp.json`; `/.well-known/mcp/server-card.json` and
`/.well-known/mcp/server-cards.json` are also probed because deployed servers
use them.

### Agent-to-Agent (A2A)
| Source | Status | Read |
|---|---|---|
| [A2A specification](https://a2a-protocol.org/latest/specification/) | 200 | listing |
| [A2A agent discovery](https://a2a-protocol.org/latest/topics/agent-discovery/) | 200 | listing |

### Agent Skills
| Source | Status | Read |
|---|---|---|
| <https://agentskills.io/> | 200 | direct |
| [Agent Skills specification](https://agentskills.io/specification) | 200 | direct |
| [github.com/agentskills/agentskills](https://github.com/agentskills/agentskills) | 200 | listing |
| [Claude Code skills documentation](https://code.claude.com/docs/en/skills) | 200 | listing |
| `https://schemas.agentskills.io/discovery/0.2.0/schema.json` | **NXDOMAIN** | direct |

> **Caveat worth knowing.** The `$schema` URL that Cloudflare's own
> `index.json` points at does not resolve — `schemas.agentskills.io` returns
> NXDOMAIN, while the apex `agentskills.io` resolves fine. The published
> Agent Skills specification covers the `SKILL.md` folder format; it does not
> define a `/.well-known/agent-skills/index.json` discovery index. That index
> is therefore a **de-facto convention observed in deployment**, not a
> ratified spec, and the `$schema` string in `assets/well-known/agent-skills/index.json`
> is a convention marker rather than a fetchable document. Expect it to move.

### WebMCP
| Source | Status | Read |
|---|---|---|
| [github.com/webmachinelearning/webmcp](https://github.com/webmachinelearning/webmcp) | 200 | listing |
| [Patrick Brosset — WebMCP updates and next steps (2026-02-23)](https://patrickbrosset.com/articles/2026-02-23-webmcp-updates-clarifications-and-next-steps/) | 200 | listing |

Source of the API-surface caveat baked into `assets/snippets/webmcp.js`: the
getter moved from `navigator` to `document` in the May 2026 draft, and
`navigator.modelContext` is marked deprecated in Chromium 150.

### Agentic Resource Discovery
| Source | Status | Read |
|---|---|---|
| [ARD specification](https://agenticresourcediscovery.org/spec/) | 200 | **direct** |
| [Google Developers Blog — announcing ARD](https://developers.googleblog.com/announcing-the-agentic-resource-discovery-specification/) | 200 | listing |

The full `ai-catalog.json` schema in `assets/well-known/ai-catalog.json` — the
`specVersion` / `host` / `entries` shape, the `urn:air:` identifier format, the
strict `url`-xor-`data` rule and the four discovery mechanisms — was taken from
the specification directly. v0.9 draft, Apache 2.0, announced 2026-06-17 by
Google with Microsoft, GitHub, Hugging Face, Cisco, Salesforce, NVIDIA and
Databricks.

### auth.md
| Source | Status | Read |
|---|---|---|
| [github.com/workos/auth.md](https://github.com/workos/auth.md) | 200 | listing |
| [WorkOS — the auth.md file](https://workos.com/auth-md/docs/auth-md) | 200 | listing |
| [PostHog — agent discovery (a live adopter)](https://posthog.com/docs/settings/agent-discovery) | — | listing |

Composes RFC 9728 and ID-JAG; not tied to WorkOS infrastructure. Two flows:
agent-verified (ID-JAG, synchronous) and user-claimed (OTP).

---

## 4. Agentic commerce

| Protocol | Source | Status | Read |
|---|---|---|---|
| x402 | <https://www.x402.org/> · [coinbase/x402](https://github.com/coinbase/x402) | 200 | listing |
| ACP | <https://www.agenticcommerce.dev/> | 200 | listing |
| UCP | <https://universalcommerce.org/> | 200 | listing |
| AP2 | <https://ap2-protocol.org/> | 200 | listing |
| MPP | <https://machinepayments.org/> | 200 | listing |
| Overview | [awesome-agentic-commerce](https://github.com/xpaysh/awesome-agentic-commerce) | — | listing |
| Overview | [Descope — developer's guide to agentic commerce](https://www.descope.com/blog/post/developer-guide-agentic-commerce) | — | listing |

Positioning used in `references/checks.md`, from the overview sources: ACP
(OpenAI + Stripe) is behind ChatGPT Instant Checkout; UCP (Google, with
Shopify, Etsy, Target, Walmart) covers multi-merchant discovery and checkout;
x402 (Coinbase) revives HTTP 402 for per-call stablecoin payments; MPP
(Stripe/Tempo) is payment-method agnostic; AP2 (Google) proves an agent is
authorised to pay and layers on A2A.

The commerce probe paths (`/.well-known/acp.json`, `/.well-known/ucp`,
`/openapi.json` for MPP, HTTP 402 on `/`, `/api`, `/api/v1`) were **not** taken
from these specs — they were observed in the reference scanner's own evidence
trail. See `METHODOLOGY.md` §2.

---

## 5. Sites scanned for validation

Used only as test fixtures, to confirm this scanner produces the same level and
next-level requirements as the reference. No content from them is redistributed.

`stripe.com` · `www.baccan.it` · `developers.cloudflare.com` ·
`isitagentready.com`

---

## 6. Third-party services this tool calls at runtime

| Service | When | Why |
|---|---|---|
| `cloudflare-dns.com/dns-query` | every scan | DNS-over-HTTPS JSON for `dnsAid` and `ard`. No stdlib DNS resolver exists in Python. |
| `isitagentready.com/api/scan` | only with `--remote` | Cross-check against the reference implementation. |

Both are third-party endpoints: a scan with `--remote` sends the target URL to
Cloudflare. Every other request goes only to the site being scanned.
