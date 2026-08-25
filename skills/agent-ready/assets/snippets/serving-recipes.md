# Serving recipes: Markdown negotiation and Link headers

The two checks that need server config rather than a new file. Pick the row
that matches the stack, copy, adapt the domain.

---

## 1. Markdown content negotiation

**Goal:** `GET /page` with `Accept: text/markdown` returns markdown;
a browser still gets HTML. Always send `Vary: Accept`, or a CDN will cache one
representation and serve it to the wrong audience.

**Test it:**

```bash
curl -sD - -o /dev/null -H "Accept: text/markdown" https://example.com/
# want: HTTP/2 200 / content-type: text/markdown / vary: accept
```

### Cloudflare (zero code)

Enable **Markdown for Agents** in the dashboard (Rules → Settings) or via the
API. Cloudflare converts HTML to markdown at the edge and sets `Vary: Accept`.
Docs: <https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/>

### nginx (pre-rendered `.md` files next to the HTML)

```nginx
map $http_accept $wants_md {
    default          0;
    "~*text/markdown" 1;
}

server {
    location / {
        add_header Vary Accept always;
        if ($wants_md) {
            rewrite ^/(.*)$ /md/$1.md last;
        }
        try_files $uri $uri/ /index.html;
    }

    location /md/ {
        internal;
        default_type text/markdown;
        add_header Vary Accept always;
    }
}
```

### Apache (.htaccess)

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteCond %{HTTP:Accept} text/markdown [NC]
  RewriteCond %{DOCUMENT_ROOT}/md%{REQUEST_URI}.md -f
  RewriteRule ^(.*)$ /md/$1.md [L]
</IfModule>
Header always append Vary Accept
AddType text/markdown .md
```

### Express / Node

```js
app.use((req, res, next) => {
  res.vary("Accept");
  if (req.accepts(["text/html", "text/markdown"]) === "text/markdown") {
    const md = renderMarkdownFor(req.path);   // your renderer
    if (md) return res.type("text/markdown; charset=utf-8").send(md);
  }
  next();
});
```

### Next.js (middleware.ts)

```ts
import { NextResponse, type NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const accept = req.headers.get("accept") ?? "";
  const wantsMd =
    /text\/markdown/.test(accept) && accept.indexOf("text/markdown") < accept.indexOf("text/html");

  if (wantsMd) {
    const url = req.nextUrl.clone();
    url.pathname = `/md${req.nextUrl.pathname}`.replace(/\/$/, "/index") + ".md";
    const res = NextResponse.rewrite(url);
    res.headers.set("Vary", "Accept");
    return res;
  }
  const res = NextResponse.next();
  res.headers.set("Vary", "Accept");
  return res;
}

export const config = { matcher: ["/((?!_next|api|.*\\.).*)"] };
```

### Cloudflare Worker (in front of any origin)

```js
export default {
  async fetch(request, env) {
    const accept = request.headers.get("accept") || "";
    const res = await fetch(request);
    const out = new Response(res.body, res);
    out.headers.append("Vary", "Accept");
    if (!/text\/markdown/.test(accept)) return out;

    const mdURL = new URL(request.url);
    mdURL.pathname = mdURL.pathname.replace(/\/$/, "/index") + ".md";
    const md = await fetch(mdURL.toString());
    if (!md.ok) return out;
    return new Response(md.body, {
      headers: {
        "content-type": "text/markdown; charset=utf-8",
        vary: "Accept",
        "cache-control": out.headers.get("cache-control") || "public, max-age=300",
      },
    });
  },
};
```

### Netlify (Edge Function)

`_redirects` cannot branch on `Accept` — it only supports Country, Language and
Role conditions — so negotiation needs an Edge Function.

`netlify/edge-functions/markdown.ts`:

```ts
import type { Config, Context } from "@netlify/edge-functions";

export default async (request: Request, context: Context) => {
  const accept = request.headers.get("accept") ?? "";
  const wantsMd =
    accept.includes("text/markdown") &&
    (!accept.includes("text/html") ||
      accept.indexOf("text/markdown") < accept.indexOf("text/html"));

  if (!wantsMd) {
    const res = await context.next();
    res.headers.append("Vary", "Accept");
    return res;
  }

  // Serve the pre-rendered markdown twin: /about.html -> /md/about.md
  const url = new URL(request.url);
  const slug = url.pathname.replace(/\.html$/, "").replace(/\/$/, "") || "/index";
  const md = await fetch(new URL(`/md${slug}.md`, url.origin));

  if (!md.ok) {
    const res = await context.next();
    res.headers.append("Vary", "Accept");
    return res;
  }
  return new Response(md.body, {
    headers: {
      "content-type": "text/markdown; charset=utf-8",
      vary: "Accept",
      "cache-control": "public, max-age=300",
    },
  });
};

export const config: Config = { path: "/*", excludedPath: ["/md/*", "/*.xml", "/*.txt", "/*.json"] };
```

Generate the `/md/**.md` twins at build time from the same source as the HTML —
a markdown twin that drifts from the page is worse than none. If the site is
already built from markdown, just copy the sources into `/md/`.

### Static hosts with no negotiation (GitHub Pages, plain S3)

You cannot negotiate. Do the next best thing and publish parallel `.md` routes,
then advertise them:

```html
<link rel="alternate" type="text/markdown" href="/page.md">
```

The scanner scores this as a partial pass, not a full one.

---

## 2. Link response headers

**Goal:** the homepage response carries a `Link:` header pointing at your
machine-readable surfaces. Agents that never parse HTML still find them.

**Test it:**

```bash
curl -sD - -o /dev/null https://example.com/ | grep -i '^link:'
```

### Cloudflare Pages / Netlify (`_headers` file at the site root)

```
/*
  Link: </.well-known/mcp.json>; rel="service-desc", </.well-known/agent-skills/index.json>; rel="describedby", </.well-known/api-catalog>; rel="api-catalog", </.well-known/ai-catalog.json>; rel="ai-catalog"
  Vary: Accept
```

### nginx

```nginx
add_header Link '</.well-known/mcp.json>; rel="service-desc", </.well-known/agent-skills/index.json>; rel="describedby", </.well-known/api-catalog>; rel="api-catalog", </.well-known/ai-catalog.json>; rel="ai-catalog"' always;
```

### Apache

```apache
Header always append Link "</.well-known/mcp.json>; rel=\"service-desc\""
Header always append Link "</.well-known/api-catalog>; rel=\"api-catalog\""
Header always append Link "</.well-known/ai-catalog.json>; rel=\"ai-catalog\""
```

### Express

```js
app.use((_req, res, next) => {
  res.setHeader("Link", [
    '</.well-known/mcp.json>; rel="service-desc"',
    '</.well-known/agent-skills/index.json>; rel="describedby"',
    '</.well-known/api-catalog>; rel="api-catalog"',
    '</.well-known/ai-catalog.json>; rel="ai-catalog"',
  ].join(", "));
  next();
});
```

---

## 3. Content types for the `.well-known` files

Getting these wrong turns a published file into a failed check.

| Path | Content-Type |
|---|---|
| `/.well-known/api-catalog` (no extension) | `application/linkset+json` |
| `/.well-known/ai-catalog.json` | `application/json` |
| `/.well-known/mcp.json` | `application/json` |
| `/.well-known/agent-card.json` | `application/json` |
| `/.well-known/agent-skills/index.json` | `application/json` |
| `/auth.md` | `text/markdown; charset=utf-8` |
| `/llms.txt` | `text/plain; charset=utf-8` (or `text/markdown`) |
| `/.well-known/security.txt` | `text/plain; charset=utf-8` |
| `/robots.txt` | `text/plain; charset=utf-8` |

nginx:

```nginx
location = /.well-known/api-catalog { default_type application/linkset+json; }
location = /auth.md               { default_type text/markdown; charset utf-8; }
location = /llms.txt              { default_type text/plain;    charset utf-8; }
```
