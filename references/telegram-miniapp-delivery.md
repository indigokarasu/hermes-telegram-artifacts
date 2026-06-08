# Telegram Mini App Delivery Patterns

## Settled Architecture

The artifact delivery pipeline has three layers:

1. **Agent generates HTML** → saves to `~/.hermes/artifacts/<id>.html`
2. **Adapter sends `web_app` button** → user taps → Mini App opens full-screen
3. **Artifact server serves HTML** → `https://<host>/artifact/<id>` returns the file

The `web_app` button is the proven, reliable approach. Don't deviate from it without strong reason.

## Delivery Methods (ranked by reliability)

### 1. `web_app` Button (recommended)
```python
InlineKeyboardButton(text=title, web_app=WebAppInfo(url=f"https://{host}/artifact/{id}"))
```
- Opens full-screen in Telegram WebView
- Works on all platforms (iOS, Android, desktop)
- No special BotFather config needed beyond enabling Mini Apps
- This is what the adapter uses

### 2. Deep Link with `mode=compact` (alternative)
```
https://t.me/<bot>?startapp=artifact:<id>&mode=compact
```
- Opens at half-screen height
- Requires Main Mini App configured in BotFather (`/newapp`)
- Dashboard must consume `tg.startParam` to navigate to the artifact
- URL button: `InlineKeyboardButton(url=f"https://t.me/{bot}?startapp=artifact:{id}&mode=compact")`
- **Caveat:** URL buttons don't trigger `answerWebAppQuery`, so no inline card feedback

### 3. `answerWebAppQuery` (don't use)
- Requires `query_id` from `tg.initDataUnsafe.query_id`
- `query_id` is ONLY available when the Mini App was opened via a `web_app` button
- The resulting inline result card is a weak preview — just shows title + description
- Not worth the complexity. The `web_app` button IS the UX.

## BotFather Setup

For basic `web_app` buttons:
1. Create bot via `/newbot`
2. Enable Mini Apps: `/newapp` or set menu button via `/setmenubutton`
3. Set the Mini App URL to your public HTTPS endpoint

For deep links with `mode=compact`:
1. Same as above, PLUS configure the Main Mini App via `/newapp`
2. The Main Mini App URL becomes the default when users tap the bot's menu button
3. `startapp` parameter is passed as `tg.startParam` / `tg.initDataUnsafe.start_param`

## Environment Variables

**Auto-loaded from `~/.hermes/.env` (via python-dotenv):**
- `TELEGRAM_BOT_TOKEN` — the bot token. Already present if Hermes is configured.

**Required as CLI args (not env vars):**
- `host` — public hostname for the artifact server (e.g., `your-domain.com`)
- `chat_id` — Telegram chat to send to

**Optional env vars:**
- `HERMES_ARTIFACT_CHAT` — default chat_id (avoids passing as arg)
- `HERMES_ARTIFACT_THREAD` — default thread_id

**Removed (no longer needed):**
- `HERMES_DASHBOARD_HOST` — was used for `answerWebAppQuery` inline result URLs. Dropped along with inline results. Host is now a CLI arg to `send-artifact.py`.
- `HERMES_BOT_TOKEN` — was a separate env var. Now auto-discovered from `~/.hermes/.env`.

## Registering Artifacts

Before sending, the HTML must be registered with the artifact server:

```bash
# Using register-artifact.py (just registers, doesn't send):
python3 ~/.hermes/skills/creative/artifact-builder/scripts/register-artifact.py \
  /tmp/thing.html "Title"
# Returns: Registered: <hex_id> — Title

# Using send-artifact.py (registers + sends web_app button):
python3 ~/.hermes/skills/creative/artifact-builder/scripts/send-artifact.py \
  /tmp/thing.html "Title" <host> [chat_id] [thread_id]
```

The artifact server stores HTML on disk at `~/.hermes/artifacts/<id>.html` and serves it at `https://<host>/artifact/<id>`.

## Standalone Version

For users NOT running Hermes, a portable version lives at:
https://github.com/camel-vibe/hermes-telegram-artifacts

Same scripts, zero Hermes dependencies. Just needs Python 3.11+, `python-telegram-bot`, `python-dotenv`, and `requests`.
