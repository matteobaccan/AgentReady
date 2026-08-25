# Agent registration for {{SITE_NAME}}

This document tells an AI agent how to obtain scoped credentials for
{{SITE_NAME}} on behalf of a user, without scraping the human sign-up form.

Protocol: auth.md - https://github.com/workos/auth.md
Machine-readable source of truth: `/.well-known/oauth-protected-resource`
(RFC 9728) and `/.well-known/oauth-authorization-server` (RFC 8414).

## Supported flows

- `agent_verified` - the agent presents an ID-JAG assertion; synchronous, no
  human interaction required.
- `user_claimed` - the agent registers, then the user claims the resulting
  credential with a one-time code sent to their email.

## Endpoints

| Purpose | URL |
|---|---|
| Authorization server metadata | `https://{{DOMAIN}}/.well-known/oauth-authorization-server` |
| Protected resource metadata | `https://{{DOMAIN}}/.well-known/oauth-protected-resource` |
| Agent registration | `https://{{AUTH_DOMAIN}}/agents/register` |
| Credential claim | `https://{{AUTH_DOMAIN}}/agents/claim` |
| Revocation | `https://{{AUTH_DOMAIN}}/agents/revoke` |

## Scopes

| Scope | Grants |
|---|---|
| `{{scope.read}}` | Read {{resource}} owned by the user |
| `{{scope.write}}` | Create and update {{resource}} |

## Rate limits and rules

- {{N}} requests/minute per registered agent.
- Agents MUST send a descriptive `User-Agent` and, where supported, sign
  requests with Web Bot Auth (RFC 9421).
- Credentials are user-scoped and revocable by the user at any time from
  {{https://DOMAIN/settings/agents}}.

## Contact

{{security@DOMAIN}} for abuse, {{support@DOMAIN}} for integration questions.
