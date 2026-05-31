#!/usr/bin/env python3
"""Register an artifact and send a web_app button — one command.

Usage:
  # From file (everything auto-detected from env/session context)
  python3 send-artifact.py /tmp/thing.html "Title"

  # Explicit overrides
  python3 send-artifact.py /tmp/thing.html "Title" <host> <chat_id> [thread_id]

Env (all auto-set by the gateway, no manual config needed):
  TELEGRAM_BOT_TOKEN           — from ~/.hermes/.env (auto-loaded)
  HERMES_DASHBOARD_HOST        — public hostname
  HERMES_SESSION_CHAT_ID       — current chat_id (bridged from ContextVar)
  HERMES_SESSION_THREAD_ID     — current thread_id (bridged from ContextVar)

The agent never needs to figure out IDs — just pass HTML + title.
The gateway bridges session ContextVars into subprocess env, so the
correct chat and thread are always available.

Exit 0 on success. Prints: OK id=<hex> message_id=<n>
"""

import asyncio
import os
import sys


def load_env():
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/.hermes/.env"))


def _ensure_server(port: int = 9877):
    """Start artifact-server.py if not already running."""
    import socket
    import subprocess

    # Quick check — is something listening on the port?
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=2)
        s.close()
        return  # server is up
    except (ConnectionRefusedError, OSError):
        pass

    # Start artifact-server.py from the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_py = os.path.join(script_dir, "artifact-server.py")
    if not os.path.exists(server_py):
        return  # can't start, let register() fail with a clear error

    subprocess.Popen(
        [sys.executable, server_py, "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    # Wait for it to come up (max 5s)
    import time
    for _ in range(50):
        time.sleep(0.1)
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=1)
            s.close()
            return
        except (ConnectionRefusedError, OSError):
            pass


def register(html: str, title: str, port: int = 9877) -> str:
    """Register artifact, return hex ID."""
    import requests

    _ensure_server(port)

    resp = requests.post(
        f"http://localhost:{port}/artifact",
        json={"title": title, "html": html},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["id"]


async def send_button(artifact_id: str, chat_id: int, thread_id: int | None, title: str, host: str):
    """Send web_app button to Telegram."""
    from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not found in ~/.hermes/.env", file=sys.stderr)
        sys.exit(1)

    bot = Bot(token=token)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=title, web_app=WebAppInfo(url=f"https://{host}/artifact/{artifact_id}"))]
    ])

    label = title.replace("Open ", "")
    kwargs = {"chat_id": chat_id, "text": f"{label} — tap below to open:", "reply_markup": kb}
    if thread_id is not None:
        kwargs["message_thread_id"] = thread_id

    msg = await bot.send_message(**kwargs)
    return msg.message_id


def main():
    load_env()

    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    html_path = sys.argv[1]
    title = sys.argv[2]

    # Host: CLI arg > env var
    host = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("HERMES_DASHBOARD_HOST", "")
    if not host:
        print("ERROR: host required (pass as arg or set HERMES_DASHBOARD_HOST)", file=sys.stderr)
        sys.exit(1)

    # Chat ID: CLI arg > session env > legacy env
    chat_id = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] not in ("", "none") else None
    if chat_id is None:
        for key in ("HERMES_SESSION_CHAT_ID", "HERMES_ARTIFACT_CHAT"):
            raw = os.environ.get(key, "")
            if raw and raw not in ("", "none"):
                chat_id = int(raw)
                break

    # Thread ID: CLI arg > session env > legacy env
    thread_id = int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] not in ("", "none") else None
    if thread_id is None:
        for key in ("HERMES_SESSION_THREAD_ID", "HERMES_ARTIFACT_THREAD"):
            raw = os.environ.get(key, "")
            if raw and raw not in ("", "none", "0"):
                thread_id = int(raw)
                break

    if chat_id is None:
        print("ERROR: chat_id required (pass as arg or set HERMES_ARTIFACT_CHAT)", file=sys.stderr)
        sys.exit(1)

    # Read HTML
    if html_path == "-":
        html = sys.stdin.read()
    else:
        with open(html_path) as f:
            html = f.read()

    # Register
    artifact_id = register(html, title)

    # Send
    msg_id = asyncio.run(send_button(artifact_id, chat_id, thread_id, title, host))

    print(f"OK id={artifact_id} message_id={msg_id} chat={chat_id} thread={thread_id or 'none'}")


if __name__ == "__main__":
    main()
