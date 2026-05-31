#!/usr/bin/env python3
"""Save an artifact HTML file to the artifacts directory.

Usage:
  python3 deliver-artifact.py <artifact_id> <html_file>
  python3 deliver-artifact.py <artifact_id> -          # read from stdin

This script only saves the file. The Telegram adapter handles sending
the web_app button — no bot API calls needed here.
"""

import os
import sys

ARTIFACTS_DIR = os.path.expanduser("~/.hermes/artifacts")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    artifact_id = sys.argv[1]
    html_path = sys.argv[2]

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    if html_path == "-":
        html = sys.stdin.read()
    else:
        with open(html_path) as f:
            html = f.read()

    out = os.path.join(ARTIFACTS_DIR, f"{artifact_id}.html")
    with open(out, "w") as f:
        f.write(html)

    print(f"OK path={out}")


if __name__ == "__main__":
    main()
