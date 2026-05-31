# WebUI Artifact Route (OBSOLETE)

**This approach is obsolete.** Artifacts are now served by the standalone `artifact-server.py` bundled with the skill. No webui patches needed.

Historical note: previously, the `/artifact/<id>` GET route had to be manually added to `/root/.local/share/hermes-webui/webui/api/routes.py`. This is no longer required — the artifact server handles all serving independently.

If you see this reference in old documentation, ignore it. The current approach is:
1. Run `artifact-server.py` (port 9877)
2. Expose via reverse proxy
3. Done
