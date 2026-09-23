import os
import secrets
import sqlite3
import textwrap
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("SHARE_DATA_DIR", Path.home() / ".local/share/text-generator/shares"))
DB_PATH = DATA_DIR / "shared_results.sqlite3"
OG_DIR = DATA_DIR / "og"
BG_PATH = ROOT / "static/img/og/share-bg.jpg"
FONT_BOLD = ROOT / "questions/assets/Sora-700.ttf"
FONT_REG = ROOT / "questions/assets/Sora-400.ttf"
MAX_OUTPUT = 6000
MAX_INPUT = 1000
RATE_WINDOW = 600
RATE_MAX = 20

router = APIRouter()
_lock = threading.Lock()
_hits = defaultdict(deque)


def _db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS shared_results (id TEXT PRIMARY KEY, tool TEXT NOT NULL, input TEXT, output TEXT NOT NULL, created REAL NOT NULL, views INTEGER NOT NULL DEFAULT 0)"
    )
    return conn


def _client_ip(request: Request) -> str:
    return request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "?")


def _rate_limited(ip: str) -> bool:
    now = time.time()
    with _lock:
        q = _hits[ip]
        while q and now - q[0] > RATE_WINDOW:
            q.popleft()
        if len(q) >= RATE_MAX:
            return True
        q.append(now)
        return False


def _tools():
    from questions.tool_fixtures import tools_fixtures

    return tools_fixtures


def get_share(share_id: str, count_view: bool = True):
    if not share_id.replace("-", "").replace("_", "").isalnum() or len(share_id) > 32:
        return None
    with _lock:
        conn = _db()
        try:
            row = conn.execute("SELECT id, tool, input, output, created FROM shared_results WHERE id = ?", (share_id,)).fetchone()
            if row and count_view:
                conn.execute("UPDATE shared_results SET views = views + 1 WHERE id = ?", (share_id,))
                conn.commit()
        finally:
            conn.close()
    if not row:
        return None
    tool = _tools().get(row[1], {})
    return {
        "id": row[0],
        "tool": row[1],
        "tool_name": tool.get("name", row[1].replace("-", " ").title()),
        "tool_description": tool.get("description", ""),
        "input": row[2] or "",
        "output": row[3],
        "created": row[4],
    }


@router.post("/api/share")
async def create_share(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    tool = str(body.get("tool", "")).strip()
    output = str(body.get("output", "")).strip()
    user_input = str(body.get("input", "") or "").strip()
    if tool not in _tools():
        raise HTTPException(status_code=400, detail="Unknown tool")
    if not output:
        raise HTTPException(status_code=400, detail="Nothing to share")
    if _rate_limited(_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many shares, try again later")
    share_id = secrets.token_urlsafe(9)
    with _lock:
        conn = _db()
        try:
            conn.execute(
                "INSERT INTO shared_results (id, tool, input, output, created) VALUES (?, ?, ?, ?, ?)",
                (share_id, tool, user_input[:MAX_INPUT], output[:MAX_OUTPUT], time.time()),
            )
            conn.commit()
        finally:
            conn.close()
    return JSONResponse({"id": share_id, "url": f"https://text-generator.io/s/{share_id}"})


def _render_og(share, path: Path):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(BG_PATH).convert("RGB")
    d = ImageDraw.Draw(img)
    title_font = ImageFont.truetype(str(FONT_BOLD), 50)
    body_font = ImageFont.truetype(str(FONT_REG), 34)
    small_font = ImageFont.truetype(str(FONT_BOLD), 26)
    d.text((90, 160), share["tool_name"], font=title_font, fill="#ff9a62")
    snippet = " ".join(share["output"].split())
    lines = []
    for line in textwrap.wrap(snippet, width=52):
        while d.textlength(line, font=body_font) > 1020 and len(line) > 10:
            line = line[:-2]
        lines.append(line)
        if len(lines) == 6:
            break
    if len(lines) == 6 and len(" ".join(lines)) < len(snippet):
        lines[-1] = lines[-1].rstrip(" .,") + "..."
    y = 250
    for line in lines:
        d.text((90, y), line, font=body_font, fill="#e2e8f0")
        y += 50
    d.text((90, 560), "Try it free at text-generator.io", font=small_font, fill="#8fb3e0")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    img.save(tmp, "JPEG", quality=85)
    tmp.replace(path)


@router.get("/s/{share_id}/og.jpg")
async def share_og(share_id: str):
    path = OG_DIR / f"{share_id}.jpg"
    if not path.exists():
        share = get_share(share_id, count_view=False)
        if not share:
            raise HTTPException(status_code=404, detail="Not found")
        _render_og(share, path)
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})
