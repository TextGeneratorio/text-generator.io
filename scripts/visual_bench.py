#!/usr/bin/env python
"""Visual bench: screenshot key funnel pages for before/after review.

Usage:
  .venv/bin/python scripts/visual_bench.py --base https://text-generator.io --out visual_bench/prod
  .venv/bin/python scripts/visual_bench.py --base http://localhost:8083 --out visual_bench/local
"""
import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PAGES = [
    ("home", "/"),
    ("subscribe", "/subscribe"),
    ("signup", "/signup"),
    ("login", "/login"),
    ("playground", "/playground"),
    ("use-cases", "/use-cases"),
    ("speech-to-text", "/speech-to-text"),
    ("text-to-speech", "/text-to-speech"),
    ("tools", "/tools"),
    ("docs", "/docs"),
]

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://text-generator.io")
    ap.add_argument("--out", default="visual_bench/out")
    ap.add_argument("--pages", default="", help="comma-separated subset of page names")
    ap.add_argument("--full-page", action="store_true", default=True)
    args = ap.parse_args()

    subset = {p for p in args.pages.split(",") if p}
    pages = [(n, p) for n, p in PAGES if not subset or n in subset]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    failures = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for vp_name, vp in VIEWPORTS.items():
            ctx = browser.new_context(viewport=vp)
            page = ctx.new_page()
            for name, path in pages:
                url = args.base.rstrip("/") + path
                try:
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(800)
                    dest = out / f"{name}-{vp_name}.png"
                    page.screenshot(path=str(dest), full_page=args.full_page)
                    print(f"OK {dest}")
                except Exception as e:
                    failures.append((url, vp_name, str(e)[:120]))
                    print(f"FAIL {url} [{vp_name}]: {e}", file=sys.stderr)
            ctx.close()
        browser.close()

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
