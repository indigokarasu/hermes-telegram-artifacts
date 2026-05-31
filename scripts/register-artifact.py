#!/usr/bin/env python3
"""Register an artifact with the Hermes Mini App.

Usage: python3 register-artifact.py <html_file> "Title Here"
   or: echo '<html>...</html>' | python3 register-artifact.py - "Title Here"

Writes the HTML file to /root/.hermes/artifacts/ and POSTs to the artifact server.
"""
import json, sys, urllib.request
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: register-artifact.py <html_file|-> \"Title\"")
    print("  Use - for stdin")
    sys.exit(1)

html_path = sys.argv[1]
title = sys.argv[2]

if html_path == "-":
    html = sys.stdin.read()
else:
    html = Path(html_path).read_text(encoding="utf-8")

# Save to artifacts dir
artifacts_dir = Path("/root/.hermes/artifacts")
artifacts_dir.mkdir(parents=True, exist_ok=True)

data = json.dumps({"title": title, "html": html}).encode()
req = urllib.request.Request(
    "http://localhost:9877/artifact",
    data=data,
    headers={"Content-Type": "application/json"},
)
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print(f"Registered: {result['id']} — {title}")
except Exception as e:
    print(f"Failed: {e}", file=sys.stderr)
    sys.exit(1)
