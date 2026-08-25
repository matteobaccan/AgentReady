/*
 * WebMCP - expose your page's actions as tools an agent can call directly,
 * instead of making it guess at your DOM.
 *
 * Spec:  https://github.com/webmachinelearning/webmcp
 * Note:  the getter moved from `navigator` to `document` in the May 2026 draft.
 *        Feature-detect both; `navigator.modelContext` is deprecated in
 *        Chromium 150 and will be removed.
 *
 * Rules that matter in practice:
 *  - Register tools AFTER the data they need is loaded, and re-register when
 *    page state changes materially (cart contents, logged-in user).
 *  - A tool must do exactly what its description says. Agents never read your
 *    code, only the description and the schema.
 *  - Never expose a destructive action without a confirmation step.
 */

function getModelContext() {
  if (typeof document !== "undefined" && document.modelContext) return document.modelContext;
  if (typeof navigator !== "undefined" && navigator.modelContext) return navigator.modelContext;
  return null;
}

function registerAgentTools() {
  const mc = getModelContext();
  if (!mc) return; // no WebMCP-capable browser: degrade silently

  mc.provideContext({
    tools: [
      {
        name: "search_products",
        description:
          "Search the catalogue of {{SITE_NAME}} by free text and return matching " +
          "products with price and availability. Call this before adding anything to a cart.",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "Free-text search terms" },
            maxResults: { type: "integer", minimum: 1, maximum: 50, default: 10 },
          },
          required: ["query"],
        },
        async execute({ query, maxResults = 10 }) {
          const url = "/api/search?q=" + encodeURIComponent(query) + "&limit=" + maxResults;
          const res = await fetch(url, { headers: { Accept: "application/json" } });
          if (!res.ok) throw new Error("Search failed: HTTP " + res.status);
          const data = await res.json();
          return { content: [{ type: "text", text: JSON.stringify(data.results, null, 2) }] };
        },
      },
      {
        name: "get_page_summary",
        description:
          "Return the main content of the page currently open, as markdown. " +
          "Use this instead of scraping the DOM.",
        inputSchema: { type: "object", properties: {} },
        async execute() {
          const res = await fetch(location.pathname, { headers: { Accept: "text/markdown" } });
          return { content: [{ type: "text", text: await res.text() }] };
        },
      },
    ],
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", registerAgentTools);
} else {
  registerAgentTools();
}
