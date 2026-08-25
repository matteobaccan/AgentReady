#!/usr/bin/env python3
"""
Ladder derivation test.

Replays compute_level() against cached reference reports and asserts it
reproduces the level the reference assigned. This is the test that pins the
ladder rules; verify_parity.py tests the whole scanner end to end.

Using cached reports rather than live scans means this runs in milliseconds,
is deterministic, and keeps working when a fixture site changes.

    python docs/verify/verify_ladder.py
    python docs/verify/verify_ladder.py --refresh   # re-fetch the fixtures

Exit code 0 if every fixture's level is reproduced, 1 otherwise.
"""

import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures", "reference-levels.json")
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "agent-ready", "scripts"))

import agent_ready_scan as ars  # noqa: E402

API = "https://isitagentready.com/api/scan"


class Stub:
    """Minimal stand-in for Check: compute_level() only reads .status."""

    def __init__(self, status):
        self.status = status


def refresh(hosts):
    out = {}
    for host in hosts:
        sys.stderr.write("fetching %s ...\n" % host)
        req = urllib.request.Request(
            API, data=json.dumps({"url": "https://" + host}).encode(),
            headers={"Content-Type": "application/json",
                     "User-Agent": "AgentReady-ladder/1.0"}, method="POST")
        with urllib.request.urlopen(req, timeout=240) as r:
            d = json.loads(r.read().decode())
        flat = {}
        for cat in d.get("checks", {}).values():
            for k, v in cat.items():
                flat[k] = v["status"]
        out[host] = {"level": d["level"], "levelName": d["levelName"], "checks": flat}
    os.makedirs(os.path.dirname(FIXTURES), exist_ok=True)
    with open(FIXTURES, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true",
                    help="re-fetch every fixture from the reference API")
    a = ap.parse_args()

    with open(FIXTURES, encoding="utf-8") as f:
        data = json.load(f)
    if a.refresh:
        data = refresh(sorted(data))

    bad = 0
    print("%-28s %-6s %-6s  %s" % ("fixture", "ref", "ours", ""))
    print("-" * 74)
    for host in sorted(data, key=lambda h: (data[h]["level"], h)):
        row = data[host]
        by_id = dict((k, Stub(v)) for k, v in row["checks"].items())
        level, nxt, unmet = ars.compute_level(by_id)
        ok = level == row["level"]
        if not ok:
            bad += 1
        print("%-28s L%-5d L%-5d %s" % (host, row["level"], level,
                                        "OK" if ok else "MISMATCH"))
    print()
    print("%d/%d fixtures reproduced (levels 0-5 represented)."
          % (len(data) - bad, len(data)))
    if bad:
        print("compute_level() no longer matches the reference. Re-derive the "
              "rules; see docs/METHODOLOGY.md section 2.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
