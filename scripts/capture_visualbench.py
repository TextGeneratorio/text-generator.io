#!/usr/bin/env python3
"""Capture repeatable visual states for the first-party media tools."""

from pathlib import Path
import os

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("VISUALBENCH_BASE_URL", "http://localhost:4444").rstrip("/")
OUTPUT = Path(__file__).resolve().parents[1] / "visualbench"


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)

        page.goto(f"{BASE_URL}/text-to-speech", wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=OUTPUT / "tts-studio-normal.png", animations="disabled")

        page.locator("#tts-text").fill("Welcome to the f")
        page.evaluate("window.__ttsOpenAutocomplete()")
        page.wait_for_timeout(1000)
        if not page.locator("#tts-typeahead").is_visible():
            raise RuntimeError("TTS autocomplete did not open")
        page.locator("#tts-typeahead").hover()
        page.screenshot(path=OUTPUT / "tts-studio-autocomplete-open.png", animations="disabled")

        page.goto(f"{BASE_URL}/tools/text-to-image", wait_until="networkidle")
        page.screenshot(path=OUTPUT / "text-to-image-normal.png", animations="disabled")

        page.goto(f"{BASE_URL}/tools", wait_until="networkidle")
        page.screenshot(path=OUTPUT / "tools-directory.png", animations="disabled")

        page.goto(f"{BASE_URL}/playground", wait_until="networkidle")
        page.locator("#open-code-button").click()
        page.locator("#code-example-dialog").wait_for(state="visible")
        page.screenshot(path=OUTPUT / "playground-code-dialog.png", animations="disabled")

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile.goto(f"{BASE_URL}/playground", wait_until="networkidle")
        mobile.screenshot(path=OUTPUT / "playground-mobile.png", animations="disabled")

        mobile.locator("#open-code-button").click()
        mobile.locator("#code-example-dialog").wait_for(state="visible")
        mobile.screenshot(path=OUTPUT / "playground-code-dialog-mobile.png", animations="disabled")

        mobile.locator("#code-example-dialog .code-dialog__close").click()
        mobile.locator("#code-example-dialog").wait_for(state="hidden")
        mobile.evaluate("showLoginModal()")
        mobile.locator("#login-modal .auth-modal-content").wait_for(state="visible")
        mobile.screenshot(path=OUTPUT / "login-dialog-mobile.png", animations="disabled")

        mobile.locator("#login-modal .auth-modal-close").click()
        mobile.evaluate("window.subscriptionModal.show()")
        mobile.locator("#subscription-modal .subscription-modal-content").wait_for(state="visible")
        mobile.screenshot(path=OUTPUT / "subscription-dialog-mobile.png", animations="disabled")
        mobile.close()
        browser.close()


if __name__ == "__main__":
    main()
