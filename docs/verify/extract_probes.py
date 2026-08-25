#!/usr/bin/env python3
"""
Re-derive the probe paths used by the reference scanner (isitagentready.com)
from its own evidence trail.

Every /api/scan response carries an `evidence` array per check, listing each
HTTP request it made. De-duplicating those across several sites reconstructs
the path list per check -- which is where the non-obvious ones came from
(/.well-known/acp.json, /.well-known/ucp, /openapi.json for MPP, ...).

    python docs/verify/extract_probes.py
    python docs/verify/extract_probes.py --sites example.com,foo.dev

Stdlib only. Hits the network; allow ~60-90s per site.
"""

import argparse
import json
import re
import sys
import urllib.request

API = "https://isitagentready.com/api/scan"
DEFAULT_SITES = ["www.baccan.it", "stripe.com", "developers.cloudflare.com",
                 "isitagentready.com"]


def scan(url):
    if not url.startswith("http"):
        url = "https://" + url
    req = urllib.request.Request(
        API, data=json.dumps({"url": url}).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": "AgentReady-probe-extractor/1.0"},
        method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", default=",".join(DEFAULT_SITES))
    ap.add_argument("--json", metavar="FILE", help="also write the raw probe map")
    a = ap.parse_args()

    probes = {}   # (category, check) -> set of "METHOD path [headers]"
    for site in [s.strip() for s in a.sites.split(",") if s.strip()]:
        sys.stderr.write("scanning %s ...\n" % site)
        try:
            rep = scan(site)
        except Exception as e:
            sys.stderr.write("  failed: %s\n" % e)
            continue
        for cat, checks in rep.get("checks", {}).items():
            for name, check in checks.items():
                for ev in check.get("evidence") or []:
                    req = ev.get("request")
                    if not req:
                        continue
                    path = re.sub(r"https?://[^/]+", "", req.get("url", ""))
                    if "dns-query" in path:
                        path = "DoH " + re.sub(r"name=[^&]*", "name=<domain>", path)
                    hdrs = req.get("headers") or {}
                    interesting = {k: v for k, v in hdrs.items()
                                   if k.lower() in ("accept", "content-type",
                                                    "mcp-protocol-version")}
                    line = "%-4s %s" % (req.get("method", "GET"), path)
                    if interesting:
                        line += "   " + json.dumps(interesting, sort_keys=True)
                    probes.setdefault((cat, name), set()).add(line)

    last_cat = None
    for (cat, name) in sorted(probes):
        if cat != last_cat:
            print("\n" + "=" * 70)
            print(cat)
            print("=" * 70)
            last_cat = cat
        print("\n  %s" % name)
        for line in sorted(probes[(cat, name)]):
            print("     " + line)
    print("\n%d checks, %d distinct probes\n"
          % (len(probes), sum(len(v) for v in probes.values())))

    if a.json:
        out = {"%s.%s" % k: sorted(v) for k, v in probes.items()}
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print("written -> " + a.json)


if __name__ == "__main__":
    main()
