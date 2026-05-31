# Artifact Server Infrastructure

Standalone artifact server (`scripts/artifact-server.py`) for serving Hermes artifacts.

## Endpoints

### GET /artifact/<id>
Serves artifact HTML with server-side injections (in order):

1. **TG lifecycle script** — Injected before `</body>`:
   - Calls `tg.ready()` to signal readiness
   - Calls `tg.exitFullscreen()` to open at half-screen (compact mode)

### POST /artifact
Register a new artifact: `{"title": "...", "html": "..."}` → `{"id": "...", "title": "...", "timestamp": "..."}`

### GET /artifacts
List all artifacts with age info.

### GET /artifacts/all
Gallery page (HTML). Latest artifact expanded with iframe, rest collapsed with expand/collapse toggle. Open and Delete buttons for each artifact.

### DELETE /artifact/<id>
Delete an artifact by ID.

## Running

```bash
# Default: 127.0.0.1:9877
python3 ~/.hermes/skills/creative/artifact-builder/scripts/artifact-server.py

# Custom host/port
python3 artifact-server.py --host 0.0.0.0 --port 8080
```

Requires Python 3.10+, stdlib only. Artifacts stored in `~/.hermes/artifacts/`.

## Exposing Publicly

The adapter sends `web_app` buttons to `https://<HERMES_DASHBOARD_HOST>/artifact/<id>`. To make this work:

1. Run the artifact server on a port (default 9877)
2. Set up a reverse proxy (nginx, Tailscale Funnel, caddy) that routes `/artifact/` to that port
3. Set `HERMES_DASHBOARD_HOST` env var to your public hostname

Example Tailscale Funnel:
```bash
tailscale funnel --bg 9877 https://your-host.example.com
```
