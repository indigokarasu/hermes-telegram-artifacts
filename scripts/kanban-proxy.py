#!/usr/bin/env python3
"""Kanban Mini App — Telegram initData auth + direct DB read/write proxy.

Serves kanban board data to a Telegram Mini App artifact.
Authenticates via Telegram initData HMAC verification.
Reads/writes directly to the kanban SQLite DB using hermes_cli.kanban_db.
"""

import hashlib
import hmac
import json
import os
import sqlite3
import sys
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN:
    for env_path in [
        Path("/root/.hermes/profiles/indigo/home/.hermes/.env"),
        Path("/root/.hermes/.env"),
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    BOT_TOKEN = line.split("=", 1)[1].strip()
                    break
        if BOT_TOKEN:
            break

ALLOWED_USER_ID = int(os.environ.get("ALLOWED_TELEGRAM_USER_ID", "8666597030"))

# Find the kanban DB
KANBAN_DB_PATH = None
for candidate in [
    Path("/root/.hermes/kanban.db"),
    Path("/root/.hermes/profiles/indigo/home/.hermes/kanban.db"),
    Path(os.environ.get("HERMES_HOME", "")) / "kanban.db" if os.environ.get("HERMES_HOME") else None,
]:
    if candidate and candidate.exists() and candidate.stat().st_size > 0:
        KANBAN_DB_PATH = str(candidate)
        break

# Add hermes-agent to path so we can import kanban_db
sys.path.insert(0, "/root/hermes-agent")

BOARD_COLUMNS = ["triage", "todo", "scheduled", "ready", "running", "blocked", "review", "done"]

# Session tokens in memory
_session_tokens: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# initData verification
# ---------------------------------------------------------------------------

def verify_init_data(init_data: str, bot_token: str) -> dict | None:
    if not init_data or not bot_token:
        return None
    params = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    hash_value = params.pop("hash", None)
    if not hash_value:
        return None
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(key=b"WebAppData", msg=bot_token.encode(), digestmod=hashlib.sha256).digest()
    computed_hash = hmac.new(key=secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, hash_value):
        return None
    auth_date = int(params.get("auth_date", 0))
    if abs(time.time() - auth_date) > 86400:
        return None
    user_json = params.get("user")
    if user_json:
        try:
            params["user"] = json.loads(user_json)
        except (json.JSONDecodeError, TypeError):
            pass
    return params

# ---------------------------------------------------------------------------
# Kankan DB operations
# ---------------------------------------------------------------------------

def get_kb():
    """Get kanban_db module, importing it with the right DB path."""
    from hermes_cli import kanban_db as kb
    # Override DB path if needed
    if KANBAN_DB_PATH:
        kb.KANBAN_DB_PATH = Path(KANBAN_DB_PATH)
    return kb

def _conn(board=None):
    kb = get_kb()
    try:
        kb.init_db(board=board)
    except Exception:
        pass
    return kb.connect(board=board)

def _to_dict(obj):
    """Convert a dataclass or namedtuple to dict."""
    if hasattr(obj, '_asdict'):
        return obj._asdict()
    if hasattr(obj, '__dict__'):
        return dict(obj.__dict__)
    return dict(obj)

def read_board():
    from hermes_cli import kanban_db as kb
    conn = _conn()
    try:
        tasks = kb.list_tasks(conn)
        link_counts = {}
        for r in conn.execute("SELECT parent_id, child_id FROM task_links").fetchall():
            link_counts.setdefault(r["parent_id"], {"parents": 0, "children": 0})["children"] += 1
            link_counts.setdefault(r["child_id"], {"parents": 0, "children": 0})["parents"] += 1
        comment_counts = {r["task_id"]: r["n"] for r in conn.execute("SELECT task_id, COUNT(*) AS n FROM task_comments GROUP BY task_id")}
        progress = {}
        for r in conn.execute("SELECT l.parent_id AS pid, t.status AS cstatus FROM task_links l JOIN tasks t ON t.id = l.child_id").fetchall():
            p = progress.setdefault(r["pid"], {"done": 0, "total": 0})
            p["total"] += 1
            if r["cstatus"] == "done":
                p["done"] += 1
        summary_map = kb.latest_summaries(conn, [t.id for t in tasks])
        columns = {c: [] for c in BOARD_COLUMNS}
        for t in tasks:
            d = _to_dict(t)
            d["link_counts"] = link_counts.get(t.id, {"parents": 0, "children": 0})
            d["comment_count"] = comment_counts.get(t.id, 0)
            d["progress"] = progress.get(t.id)
            full = summary_map.get(t.id)
            d["latest_summary"] = full[:200] if full else None
            col = t.status if t.status in columns else "todo"
            columns[col].append(d)
        tenants = [r["tenant"] for r in conn.execute("SELECT DISTINCT tenant FROM tasks WHERE tenant IS NOT NULL ORDER BY tenant")]
        assignees = [r["assignee"] for r in conn.execute("SELECT DISTINCT assignee FROM tasks WHERE assignee IS NOT NULL AND status != 'archived' ORDER BY assignee")]
        return {"columns": columns, "tenants": tenants, "assignees": assignees}
    finally:
        conn.close()

def read_task(task_id):
    from hermes_cli import kanban_db as kb
    conn = _conn()
    try:
        task = kb.get_task(conn, task_id)
        if not task:
            return None
        d = _to_dict(task)
        d["comments"] = [_to_dict(r) for r in kb.list_comments(conn, task_id)]
        d["events"] = [_to_dict(r) for r in kb.list_events(conn, task_id)]
        d["runs"] = [_to_dict(r) for r in kb.list_runs(conn, task_id)]
        d["links"] = {"parents": kb.parent_ids(conn, task_id), "children": kb.child_ids(conn, task_id)}
        d["attachments"] = [dict(r) for r in kb.list_attachments(conn, task_id)]
        return d
    finally:
        conn.close()

def write_task(task_id, data):
    """Update a task. Returns True on success."""
    from hermes_cli import kanban_db as kb
    conn = _conn()
    try:
        task = kb.get_task(conn, task_id)
        if not task:
            return False, "task not found"

        # Status change
        new_status = data.get("status")
        if new_status and new_status != task.status:
            if new_status == "done":
                ok = kb.complete_task(conn, task_id, result=data.get("result"), summary=data.get("summary"), metadata=data.get("metadata"))
            elif new_status == "blocked":
                ok = kb.block_task(conn, task_id, reason=data.get("block_reason"))
            elif new_status == "scheduled":
                ok = kb.schedule_task(conn, task_id, reason=data.get("block_reason"))
            elif new_status == "ready":
                if task.status in ("blocked", "scheduled"):
                    ok = kb.unblock_task(conn, task_id)
                else:
                    ok, _ = kb.promote_task(conn, task_id, actor="telegram")
            elif new_status == "archived":
                ok = kb.archive_task(conn, task_id)
            elif new_status in ("todo", "triage", "running"):
                # Direct status change (not through promote_task which only goes to ready)
                conn.execute("UPDATE tasks SET status = ? WHERE id = ?",
                             (new_status, task_id))
                conn.commit()
                ok = True
            else:
                return False, f"unsupported status: {new_status}"
            if not ok:
                return False, "status update failed"

        # Assignee change
        new_assignee = data.get("assignee")
        if new_assignee is not None and new_assignee != task.assignee:
            ok = kb.assign_task(conn, task_id, new_assignee or None)
            if not ok:
                return False, "assignee update failed"

        # Priority change
        new_priority = data.get("priority")
        if new_priority is not None and new_priority != task.priority:
            conn.execute("UPDATE tasks SET priority = ? WHERE id = ?",
                         (new_priority, task_id))
            conn.commit()

        # Title change
        new_title = data.get("title")
        if new_title is not None and new_title != task.title:
            conn.execute("UPDATE tasks SET title = ? WHERE id = ?",
                         (new_title, task_id))
            conn.commit()

        # Body change
        new_body = data.get("body")
        if new_body is not None and new_body != task.body:
            conn.execute("UPDATE tasks SET body = ? WHERE id = ?",
                         (new_body, task_id))
            conn.commit()

        return True, "ok"
    finally:
        conn.close()

def create_new_task(data):
    """Create a new task. Returns (task_id, error)."""
    from hermes_cli import kanban_db as kb
    conn = _conn()
    try:
        title = data.get("title", "").strip()
        if not title:
            return None, "title is required"
        task_id = kb.create_task(
            conn,
            title=title,
            body=data.get("body", ""),
            assignee=data.get("assignee"),
            priority=data.get("priority", 0),
            workspace_kind="scratch",
        )
        # If status specified and not default (todo), move it
        status = data.get("status")
        if status and status != "todo":
            if status == "done":
                kb.complete_task(conn, task_id)
            elif status == "blocked":
                kb.block_task(conn, task_id)
            elif status == "scheduled":
                kb.schedule_task(conn, task_id)
            elif status in ("ready", "triage", "todo"):
                ok, _ = kb.promote_task(conn, task_id, actor="telegram")
        return task_id, None
    finally:
        conn.close()

def delete_task(task_id):
    from hermes_cli import kanban_db as kb
    conn = _conn()
    try:
        ok = kb.delete_task(conn, task_id)
        return ok, "ok" if ok else "task not found"
    finally:
        conn.close()

def add_new_comment(task_id, body, author="telegram"):
    from hermes_cli import kanban_db as kb
    conn = _conn()
    try:
        ok = kb.add_comment(conn, task_id, author=author, body=body)
        return ok, "ok" if ok else "failed"
    finally:
        conn.close()

def reassign_task(task_id, profile, reason=None):
    from hermes_cli import kanban_db as kb
    conn = _conn()
    try:
        ok = kb.reassign_task(conn, task_id, profile, reclaim_first=False, reason=reason)
        return ok, "ok" if ok else "cannot reassign"
    finally:
        conn.close()

# ---------------------------------------------------------------------------
# Session tokens
# ---------------------------------------------------------------------------

def validate_session_token(token: str) -> dict | None:
    data = _session_tokens.get(token)
    if not data:
        return None
    if time.time() - data.get("created_at", 0) > 3600:
        del _session_tokens[token]
        return None
    return data

# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class KanbanProxyHandler(BaseHTTPRequestHandler):
    def _json_response(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Telegram-InitData")
        self.end_headers()

    def _get_init_data(self) -> str:
        init_data = self.headers.get("X-Telegram-InitData", "")
        if not init_data:
            parsed = urllib.parse.urlparse(self.path)
            params = dict(urllib.parse.parse_qsl(parsed.query))
            init_data = params.get("initData", "")
        return init_data

    def _authenticate(self) -> dict | None:
        init_data = self._get_init_data()
        if not init_data:
            return None
        return verify_init_data(init_data, BOT_TOKEN)

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path).path
        if parsed_path == "/kanban/auth":
            self._handle_auth()
        elif parsed_path == "/kanban/tasks":
            self._handle_create_task()
        elif parsed_path.startswith("/kanban/tasks/"):
            task_id = parsed_path[len("/kanban/tasks/"):]
            # Check for sub-routes like /tasks/{id}/comments, /tasks/{id}/reassign
            if task_id.endswith("/comments"):
                real_id = task_id[:-len("/comments")]
                self._handle_add_comment(real_id)
            elif task_id.endswith("/comment"):
                real_id = task_id[:-len("/comment")]
                self._handle_add_comment(real_id)
            elif task_id.endswith("/reassign"):
                real_id = task_id[:-len("/reassign")]
                self._handle_reassign(real_id)
            elif task_id.endswith("/archive"):
                real_id = task_id[:-len("/archive")]
                self._handle_archive(real_id)
            elif task_id.endswith("/triage"):
                real_id = task_id[:-len("/triage")]
                self._handle_triage(real_id)
            else:
                self._handle_update_task(task_id)
        elif parsed_path == "/kanban/links":
            self._handle_add_link()
        else:
            self._json_response(404, {"error": "not found"})

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path).path
        if parsed_path == "/kanban/board" or parsed_path == "/kanban/board/":
            self._handle_board()
        elif parsed_path.startswith("/kanban/tasks/"):
            task_id = parsed_path[len("/kanban/tasks/"):]
            self._handle_get_task(task_id)
        elif parsed_path == "/kanban/assignees":
            self._handle_assignees()
        elif parsed_path == "/kanban/health":
            self._json_response(200, {"ok": True, "db": KANBAN_DB_PATH, "bot_token_set": bool(BOT_TOKEN)})
        else:
            self._json_response(404, {"error": "not found"})

    def do_DELETE(self):
        parsed_path = urllib.parse.urlparse(self.path).path
        if parsed_path.startswith("/kanban/tasks/"):
            task_id = parsed_path[len("/kanban/tasks/"):]
            self._handle_delete_task(task_id)
        else:
            self._json_response(404, {"error": "not found"})

    def _read_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def _handle_auth(self):
        data = self._read_body()
        init_data = data.get("initData", "")
        if not init_data:
            self._json_response(400, {"error": "missing initData"})
            return
        parsed = verify_init_data(init_data, BOT_TOKEN)
        if not parsed:
            self._json_response(403, {"error": "invalid initData"})
            return
        user = parsed.get("user", {})
        user_id = user.get("id") if isinstance(user, dict) else None
        if user_id and int(user_id) != ALLOWED_USER_ID:
            self._json_response(403, {"error": "unauthorized user"})
            return
        session_token = hashlib.sha256(f"{user_id}:{time.time()}:{BOT_TOKEN[:16]}".encode()).hexdigest()[:32]
        _session_tokens[session_token] = {"user_id": user_id, "created_at": time.time()}
        # Clean expired
        now = time.time()
        for t in [t for t, d in _session_tokens.items() if now - d.get("created_at", 0) > 3600]:
            del _session_tokens[t]
        self._json_response(200, {"ok": True, "token": session_token, "user": user})

    def _handle_board(self):
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        try:
            data = read_board()
            self._json_response(200, data)
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_get_task(self, task_id):
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        try:
            task = read_task(task_id)
            if not task:
                self._json_response(404, {"error": "task not found"})
                return
            self._json_response(200, task)
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_update_task(self, task_id):
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        data = self._read_body()
        try:
            ok, msg = write_task(task_id, data)
            if ok:
                # Read back and return updated task
                task = read_task(task_id)
                self._json_response(200, {"ok": True, "task": task})
            else:
                self._json_response(400, {"error": msg})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_create_task(self):
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        data = self._read_body()
        try:
            task_id, err = create_new_task(data)
            if err:
                self._json_response(400, {"error": err})
                return
            task = read_task(task_id)
            self._json_response(201, {"ok": True, "task": task})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_delete_task(self, task_id):
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        try:
            ok, msg = delete_task(task_id)
            if ok:
                self._json_response(200, {"ok": True})
            else:
                self._json_response(404, {"error": msg})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_add_comment(self, task_id):
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        data = self._read_body()
        body = data.get("body", "").strip()
        if not body:
            self._json_response(400, {"error": "body is required"})
            return
        user = parsed.get("user", {})
        author = user.get("first_name", "telegram") if isinstance(user, dict) else "telegram"
        try:
            ok, msg = add_new_comment(task_id, body, author)
            if ok:
                task = read_task(task_id)
                self._json_response(201, {"ok": True, "task": task})
            else:
                self._json_response(400, {"error": msg})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_reassign(self, task_id):
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        data = self._read_body()
        profile = data.get("profile", "")
        reason = data.get("reason")
        if not profile:
            self._json_response(400, {"error": "profile is required"})
            return
        try:
            ok, msg = reassign_task(task_id, profile, reason)
            if ok:
                task = read_task(task_id)
                self._json_response(200, {"ok": True, "task": task})
            else:
                self._json_response(400, {"error": msg})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_add_link(self):
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        data = self._read_body()
        from_id = data.get("from_id")
        to_id = data.get("to_id")
        if not from_id or not to_id:
            self._json_response(400, {"error": "from_id and to_id are required"})
            return
        try:
            from hermes_cli import kanban_db as kb
            conn = _conn()
            try:
                kb.link_tasks(conn, from_id, to_id)
                conn.close()
                self._json_response(201, {"ok": True})
            except Exception as e:
                try: conn.close()
                except: pass
                raise
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_triage(self, task_id):
        """Move task to triage status (demote from any status)."""
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        try:
            from hermes_cli import kanban_db as kb
            conn = _conn()
            try:
                # Set status directly to triage
                conn.execute("UPDATE tasks SET status = 'triage' WHERE id = ?", (task_id,))
                conn.commit()
                task = read_task(task_id)
                if task:
                    self._json_response(200, {"ok": True, "task": task})
                else:
                    self._json_response(404, {"error": "task not found"})
            finally:
                conn.close()
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_archive(self, task_id):
        """Archive a task."""
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        try:
            from hermes_cli import kanban_db as kb
            conn = _conn()
            try:
                ok = kb.archive_task(conn, task_id)
                if ok:
                    self._json_response(200, {"ok": True})
                else:
                    self._json_response(400, {"error": "archive failed"})
            finally:
                conn.close()
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_assignees(self):
        parsed = self._authenticate()
        if not parsed:
            self._json_response(401, {"error": "unauthenticated"})
            return
        try:
            from hermes_cli import kanban_db as kb
            conn = _conn()
            try:
                assignees = kb.known_assignees(conn)
                self._json_response(200, {"assignees": assignees})
            finally:
                conn.close()
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def log_message(self, format, *args):
        sys.stderr.write(f"[kanban-proxy] {args[0]}\n")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    port = int(os.environ.get("KANBAN_PROXY_PORT", "9878"))
    if not BOT_TOKEN:
        print("[kanban-proxy] WARNING: TELEGRAM_BOT_TOKEN not set", flush=True)
    if not KANBAN_DB_PATH:
        print("[kanban-proxy] WARNING: kanban.db not found", flush=True)
    else:
        print(f"[kanban-proxy] Kanban DB: {KANBAN_DB_PATH}", flush=True)
    server = HTTPServer(("127.0.0.1", port), KanbanProxyHandler)
    print(f"[kanban-proxy] Listening on 127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[kanban-proxy] Shutting down.", flush=True)
        server.server_close()

if __name__ == "__main__":
    main()
