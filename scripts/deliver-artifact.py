#!/usr/bin/env python3
"""Save an artifact HTML file to the artifacts directory and register it in the index.

Usage:
  python3 deliver-artifact.py <artifact_id> <html_file>
  python3 deliver-artifact.py <artifact_id> -          # read from stdin

This script saves the file and updates the index so the artifact server can list it.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ARTIFACTS_DIR = Path.home() / ".hermes" / "artifacts"
ARTIFACTS_INDEX = ARTIFACTS_DIR / "index.json"


def _load_index():
    if not ARTIFACTS_INDEX.exists():
        return {"artifacts": []}
    try:
        return json.loads(ARTIFACTS_INDEX.read_text())
    except Exception:
        return {"artifacts": []}


def _save_index(data):
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_INDEX.write_text(json.dumps(data, indent=2))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    artifact_id = sys.argv[1]
    html_path = sys.argv[2]

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    if html_path == "-":
        html = sys.stdin.read()
    else:
        with open(html_path) as f:
            html = f.read()

    out = ARTIFACTS_DIR / f"{artifact_id}.html"
    out.write_text(html, encoding="utf-8")

    # Register in index so artifact-server can list it
    ts = datetime.now(timezone.utc).isoformat()
    idx = _load_index()
    # Remove existing entry with same id (if any)
    idx["artifacts"] = [a for a in idx["artifacts"] if a.get("id") != artifact_id]
    entry = {"id": artifact_id, "title": artifact_id, "type": "html", "timestamp": ts}
    idx["artifacts"].insert(0, entry)
    idx["artifacts"] = idx["artifacts"][:50]
    _save_index(idx)

    print(f"OK path={out}")


if __name__ == "__main__":
    main()
