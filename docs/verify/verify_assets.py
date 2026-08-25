#!/usr/bin/env python3
"""
Asset integrity test: are the shipped templates actually usable?

A broken template is worse than a missing one -- it fails the very check it was
meant to fix, on someone else's site, after they deployed it. This checks the
things that would make that happen:

  * every JSON template parses
  * every SVG is well-formed XML
  * every asset SKILL.md and README.md point at exists on disk
  * no template has lost its {{PLACEHOLDER}} markers (a template with real
    values baked in would ship someone else's domain)

Offline, no dependencies, milliseconds.

    python docs/verify/verify_assets.py

Exit code 0 if everything checks out, 1 otherwise.
"""

import glob
import json
import os
import re
import sys
import xml.dom.minidom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(ROOT, "skills", "agent-ready", "assets")

# Templates that must still carry placeholders. security.txt and the snippets
# are excluded: some are complete as shipped.
MUST_TEMPLATE = ["robots.txt", "llms.txt", "auth.md",
                 os.path.join("well-known", "ai-catalog.json"),
                 os.path.join("well-known", "mcp.json"),
                 os.path.join("well-known", "agent-card.json"),
                 os.path.join("well-known", "api-catalog.json")]


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def main():
    problems = []
    checked = 0

    # 1. JSON templates parse
    for f in sorted(glob.glob(os.path.join(ASSETS, "**", "*.json"), recursive=True)):
        checked += 1
        try:
            with open(f, encoding="utf-8") as fh:
                json.load(fh)
        except Exception as e:
            problems.append("%s: invalid JSON -- %s" % (rel(f), e))

    # 2. Plugin manifests parse
    for f in sorted(glob.glob(os.path.join(ROOT, ".claude-plugin", "*.json"))):
        checked += 1
        try:
            with open(f, encoding="utf-8") as fh:
                json.load(fh)
        except Exception as e:
            problems.append("%s: invalid JSON -- %s" % (rel(f), e))

    # 3. SVGs are well-formed XML
    for f in sorted(glob.glob(os.path.join(ROOT, "docs", "assets", "*.svg"))):
        checked += 1
        try:
            xml.dom.minidom.parse(f)
        except Exception as e:
            problems.append("%s: malformed SVG -- %s" % (rel(f), e))

    # 4. Templates still look like templates
    for name in MUST_TEMPLATE:
        f = os.path.join(ASSETS, name)
        checked += 1
        if not os.path.exists(f):
            problems.append("%s: missing" % rel(f))
            continue
        with open(f, encoding="utf-8") as fh:
            body = fh.read()
        if "{{" not in body:
            problems.append("%s: no {{PLACEHOLDER}} left -- did real values get "
                            "committed into a template?" % rel(f))

    # 5. Every asset the docs point at exists
    docs = [os.path.join(ROOT, "skills", "agent-ready", "SKILL.md"),
            os.path.join(ROOT, "README.md")]
    referenced = set()
    for d in docs:
        with open(d, encoding="utf-8") as fh:
            text = fh.read()
        for m in re.finditer(r"`(assets/[A-Za-z0-9_./-]+)`", text):
            referenced.add(m.group(1))
        for m in re.finditer(r"`(skills/agent-ready/[A-Za-z0-9_./-]+\.(?:py|md))`", text):
            referenced.add(m.group(1))
    for ref in sorted(referenced):
        checked += 1
        target = os.path.join(ASSETS, ref[len("assets/"):]) if ref.startswith("assets/") \
            else os.path.join(ROOT, ref)
        if not os.path.exists(target):
            problems.append("referenced in docs but missing on disk: %s" % ref)

    # 6. The skill has the front matter a skill needs
    skill = os.path.join(ROOT, "skills", "agent-ready", "SKILL.md")
    checked += 1
    with open(skill, encoding="utf-8") as fh:
        head = fh.read(2000)
    if not head.startswith("---"):
        problems.append("SKILL.md: no YAML front matter")
    else:
        for key in ("name:", "description:"):
            if key not in head.split("---")[1]:
                problems.append("SKILL.md: front matter missing %s" % key)

    for p in problems:
        print("FAIL  " + p)
    print()
    print("%d checks, %d problem(s)." % (checked, len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
