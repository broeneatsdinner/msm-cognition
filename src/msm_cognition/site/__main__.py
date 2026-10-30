"""Serve the repository as a local site for a limited time.

  bin/site [--port N] [--hours H] [--no-browser] [--no-commit] [--no-push]

Binds 127.0.0.1 only and stops by itself after --hours (default 2; 0 runs
until Ctrl-C). Folders show their contents and README, Markdown files are
rendered, other text files are shown as source, and images are served as
they are. Dotfiles, .venv, and __pycache__ are never served.

Generated inventory pages are refreshed from the island YAML before any
Markdown page is drawn, so they are always current. Ticking a checklist box
POSTs to /__edit/checklist; see edits.py for what a click changes. Each
change is committed on its own with only the files it touched, then pushed
in the background. A file that already had uncommitted changes is still
edited but not committed, so unrelated work is never swept into a commit.

Requests must name this server in their Host header, and edits must come
from its own origin, so another web page cannot reach it.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime, timedelta
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from urllib.request import urlopen

from msm_cognition.inventory import write_outputs
from msm_cognition.site.edits import EditError, plan_edit
from msm_cognition.site.render import esc, render_markdown

REPO = Path(__file__).resolve().parents[3]
STATIC = Path(__file__).resolve().parent / "static"
HOST = "127.0.0.1"
DEFAULT_PORT = 8770
PORT_TRIES = 20
APP = "msm-cognition-site"
HIDDEN = {".venv", "__pycache__", "node_modules"}
TEXT_SUFFIXES = {
    ".py", ".json", ".yaml", ".yml", ".csv", ".txt", ".sh", ".js", ".cjs",
    ".css", ".html", ".command", ".cfg", ".toml",
}
EDIT_LOCK = threading.Lock()
PUSH_LOCK = threading.Lock()
PUSHES: list[threading.Thread] = []


def log(message: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {message}", flush=True)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def is_clean(rel: Path) -> bool:
    """True when the file is tracked and has no uncommitted changes."""
    return not git("status", "--porcelain", "--", str(rel)).stdout.strip()


def push_in_background() -> None:
    def push() -> None:
        with PUSH_LOCK:
            result = git("push", "--quiet")
            if result.returncode == 0:
                log("Pushed.")
            else:
                log("Push failed; the commit stays local: " + result.stderr.strip())

    thread = threading.Thread(target=push, daemon=True)
    PUSHES.append(thread)
    thread.start()


def resolve(url_path: str) -> Path | None:
    """Map a URL path to a file or folder in the repo, or None to refuse it."""
    path = unquote(urlsplit(url_path).path)
    if "\0" in path or "\\" in path or not path.startswith("/"):
        return None
    parts = [p for p in path.split("/") if p]
    if any(p.startswith(".") or p in HIDDEN for p in parts):
        return None
    try:
        real = REPO.joinpath(*parts).resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    return real if real.is_relative_to(REPO) else None


def breadcrumbs(rel: str) -> str:
    crumbs = ['<a href="/">msm-cognition</a>']
    parts = [p for p in rel.split("/") if p]
    for index, part in enumerate(parts):
        href = "/" + "/".join(quote(p) for p in parts[: index + 1])
        is_dir = index < len(parts) - 1 or (REPO / rel).is_dir()
        crumbs.append(f'<a href="{href}{"/" if is_dir else ""}">{esc(part)}</a>')
    return " / ".join(crumbs)


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, port: int, options: argparse.Namespace, stops_at: str, **kwargs):
        self.allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        self.origins = {f"http://{host}" for host in self.allowed_hosts}
        self.options = options
        self.stops_at = stops_at
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args) -> None:
        pass

    def send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, code: int, body: dict) -> None:
        self.send(code, json.dumps(body).encode(), "application/json")

    def page(self, title: str, rel: str, body: str) -> None:
        template = (STATIC / "page.html").read_text(encoding="utf-8")
        document = (
            template.replace("{title}", esc(title))
            .replace("{crumbs}", breadcrumbs(rel))
            .replace("{stops}", esc(self.stops_at))
            .replace("{body}", body)
        )
        self.send(200, document.encode(), "text/html; charset=utf-8")

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        if self.headers.get("Host", "") not in self.allowed_hosts:
            return self.send(404, b"Not found", "text/plain")
        url = urlsplit(self.path)
        if url.path == "/__status":
            return self.send_json(200, {"app": APP, "stops_at": self.stops_at})
        if url.path.startswith("/__static/"):
            name = url.path[len("/__static/") :]
            target = (STATIC / name).resolve()
            if target.is_file() and target.is_relative_to(STATIC):
                kind = mimetypes.guess_type(target.name)[0] or "text/plain"
                return self.send(200, target.read_bytes(), kind)
            return self.send(404, b"Not found", "text/plain")
        target = resolve(self.path)
        if target is None:
            return self.send(404, b"Not found", "text/plain")
        rel = target.relative_to(REPO).as_posix() if target != REPO else ""
        if target.is_dir():
            if not url.path.endswith("/"):
                self.send_response(301)
                self.send_header("Location", url.path + "/")
                self.end_headers()
                return None
            return self.directory(target, rel)
        if "raw" in url.query:
            return self.raw(target)
        if target.suffix == ".md":
            return self.markdown(target, rel)
        if target.suffix in TEXT_SUFFIXES or (not target.suffix and target.parent.name == "bin"):
            text = target.read_text(encoding="utf-8", errors="replace")
            body = f'<p class="meta"><a href="?raw">Raw file</a></p><pre><code>{esc(text)}</code></pre>'
            return self.page(target.name, rel, body)
        return self.raw(target)

    def raw(self, target: Path) -> None:
        kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if kind.startswith("text/") or kind in {"application/json", "application/javascript"}:
            kind += "; charset=utf-8"
        self.send(200, target.read_bytes(), kind)

    def markdown(self, target: Path, rel: str) -> None:
        with EDIT_LOCK:
            write_outputs(REPO)
        text = target.read_text(encoding="utf-8")
        self.page(target.stem, rel, render_markdown(REPO, rel, text))

    def directory(self, target: Path, rel: str) -> None:
        entries = sorted(
            (p for p in target.iterdir() if not p.name.startswith(".") and p.name not in HIDDEN),
            key=lambda p: (not p.is_dir(), p.name.lower()),
        )
        rows = []
        for entry in entries:
            name = entry.name + ("/" if entry.is_dir() else "")
            rows.append(f'<li><a href="{quote(entry.name)}{"/" if entry.is_dir() else ""}">{esc(name)}</a></li>')
        body = f'<ul class="listing">{"".join(rows)}</ul>'
        readme = target / "README.md"
        if readme.is_file():
            readme_rel = readme.relative_to(REPO).as_posix()
            body += f'<hr><article>{render_markdown(REPO, readme_rel, readme.read_text(encoding="utf-8"))}</article>'
        self.page(rel or "msm-cognition", rel, body)

    def do_POST(self) -> None:
        if self.headers.get("Host", "") not in self.allowed_hosts:
            return self.send_json(404, {"error": "not found"})
        if urlsplit(self.path).path != "/__edit/checklist":
            return self.send_json(404, {"error": "not found"})
        if self.headers.get("Origin") not in self.origins:
            return self.send_json(403, {"error": "forbidden"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(min(length, 65536)) or b"{}")
            rel = unquote(str(body["path"])).lstrip("/")
            if resolve("/" + quote(rel)) is None:
                raise EditError("That file cannot be edited.")
            with EDIT_LOCK:
                result = self.apply(rel, int(body["line"]), str(body["text"]), str(body["action"]))
        except EditError as error:
            return self.send_json(409, {"error": str(error)})
        except (KeyError, TypeError, ValueError) as error:
            return self.send_json(400, {"error": f"Bad request: {error}"})
        return self.send_json(200, result)

    def apply(self, rel: str, line: int, text: str, action: str) -> dict:
        edit = plan_edit(REPO, rel, line, text, action)
        edited = edit.path.relative_to(REPO)
        was_clean = is_clean(edited)
        edit.path.write_text(edit.text, encoding="utf-8")
        changed = [edited, *write_outputs(REPO)]
        log(edit.message)

        if self.options.no_commit:
            return {"message": edit.message, "status": "Saved (commits are off)."}
        if not was_clean:
            return {
                "message": edit.message,
                "status": f"Saved, not committed: {edited} had uncommitted changes.",
            }
        paths = [str(p) for p in changed]
        git("add", "--", *paths)
        result = git("commit", "--quiet", "-m", edit.message, "--", *paths)
        if result.returncode != 0:
            log("Commit failed: " + (result.stderr or result.stdout).strip())
            return {"message": edit.message, "status": "Saved, but the commit failed; see the terminal."}
        if self.options.no_push:
            return {"message": edit.message, "status": "Saved and committed."}
        push_in_background()
        return {"message": edit.message, "status": "Saved, committed, and pushing."}


def already_running(port: int) -> str | None:
    """The stop time of a site already serving on this port, if there is one."""
    try:
        with urlopen(f"http://{HOST}:{port}/__status", timeout=1) as response:
            status = json.loads(response.read())
    except (OSError, ValueError):
        return None
    return status.get("stops_at") if status.get("app") == APP else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Browse the repository on a local site.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--hours", type=float, default=2, help="stop after this long; 0 runs until Ctrl-C")
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser tab")
    parser.add_argument("--no-commit", action="store_true", help="save clicks without committing")
    parser.add_argument("--no-push", action="store_true", help="commit clicks without pushing")
    options = parser.parse_args(argv)

    stops = already_running(options.port)
    if stops is not None:
        url = f"http://{HOST}:{options.port}/"
        print(f"Already running at {url} (stops {stops}).", flush=True)
        if not options.no_browser:
            webbrowser.open(url)
        return 0

    stop_time = datetime.now() + timedelta(hours=options.hours)
    stops_at = f"at {stop_time:%H:%M}" if options.hours > 0 else "when you press Ctrl-C"
    write_outputs(REPO)
    for port in range(options.port, options.port + PORT_TRIES):
        try:
            handler = partial(Handler, port=port, options=options, stops_at=stops_at)
            server = ThreadingHTTPServer((HOST, port), handler)
            break
        except OSError:
            continue
    else:
        print(f"No free port in {options.port}-{options.port + PORT_TRIES - 1}.", file=sys.stderr)
        return 1

    url = f"http://{HOST}:{port}/"
    print(f"Serving the repository at {url}", flush=True)
    print(f"Stops {stops_at}. Press Ctrl-C to stop sooner.", flush=True)
    if options.hours > 0:
        timer = threading.Timer(options.hours * 3600, server.shutdown)
        timer.daemon = True
        timer.start()
    if not options.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    # Let a push that is still running finish before exiting.
    for thread in PUSHES:
        thread.join(timeout=60)
    print("Stopped.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
