#!/usr/bin/env python3
"""
Parity suite: does this scanner agree with isitagentready.com?

For each fixture it runs the local scanner and the reference API and compares
the assigned level -- the one number both tools define the same way.

It does NOT fail on differing "next level" lists. The reference's
nextLevel.requirements is a curated list of suggested fixes, not the gate:
vercel.com reaches level 5 while still failing authMd, yet authMd is listed as
a requirement for every level-4 site. This scanner instead reports the checks
that actually unblock the next rung. The two lists are printed side by side as
information.

The rules themselves are pinned by docs/verify/verify_ladder.py, which replays
compute_level() against 20 cached reference reports spanning levels 0-5.

    python docs/verify/verify_parity.py
    python docs/verify/verify_parity.py --sites example.com
    python docs/verify/verify_parity.py --quiet     # exit code only

Exit code 0 if every fixture's level matches, 1 otherwise -- usable in CI.
Stdlib only. Hits the network; allow ~60-90s per site for the reference API.
"""

import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "agent-ready", "scripts"))

import agent_ready_scan as ars  # noqa: E402

API = "https://isitagentready.com/api/scan"
FIXTURES = ["stripe.com", "www.baccan.it", "developers.cloudflare.com",
            "isitagentready.com"]


def reference(url):
    if not url.startswith("http"):
        url = "https://" + url
    req = urllib.request.Request(
        API, data=json.dumps({"url": url}).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": "AgentReady-parity/1.0"},
        method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())


def blocking(report):
    nxt = report.get("nextLevel") or {}
    return sorted(r["check"] for r in nxt.get("requirements", []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", default=",".join(FIXTURES))
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    sites = [s.strip() for s in a.sites.split(",") if s.strip()]
    rows, failures = [], 0

    for site in sites:
        if not a.quiet:
            sys.stderr.write("checking %s ...\n" % site)
        mine = ars.run_scan(site, extended=False)
        try:
            theirs = reference(site)
        except Exception as e:
            rows.append((site, mine, None, "reference API error: %s" % e))
            failures += 1
            continue

        same_level = mine["level"] == theirs.get("level")
        if not same_level:
            failures += 1
        rows.append((site, mine, theirs, None if same_level else "level"))

    if not a.quiet:
        print()
        print("%-30s %-26s %-26s %s" % ("site", "this scanner", "reference", ""))
        print("-" * 100)
        for site, mine, theirs, err in rows:
            m = "%d %s" % (mine["level"], mine["levelName"])
            if theirs is None:
                print("%-30s %-26s %-26s ERROR %s" % (site, m, "-", err))
                continue
            t = "%d %s" % (theirs.get("level", -1), theirs.get("levelName", "?"))
            print("%-30s %-26s %-26s %s" % (site, m, t,
                                            "OK" if err is None else "MISMATCH"))
            # Informational only -- see the module docstring.
            mb, tb = blocking(mine), blocking(theirs)
            if mb != tb:
                print("%-30s %-26s %-26s (advisory, not compared)"
                      % ("  next ->", ",".join(mb) or "-", ",".join(tb) or "-"))
        print()
        print("%d/%d fixtures match on level." % (len(sites) - failures, len(sites)))
        if failures:
            print("A level mismatch means a draft spec moved or a check "
                  "regressed. Run docs/verify/verify_ladder.py to see whether "
                  "the ladder rules themselves still hold, then see "
                  "docs/METHODOLOGY.md section 2.")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
