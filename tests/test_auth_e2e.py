"""
E2E tests for authentication flows (signup, login, logout).
Uses Playwright for browser automation.

Run with: pytest tests/test_auth_e2e.py -v
"""

import re
import time

import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8083"


def generate_test_email():
    """Generate a unique test email address."""
    return f"e2e_test_{int(time.time())}@example.com"


class TestSignupE2E:
    """E2E tests for the signup flow."""

    def test_signup_page_loads(self, page: Page):
        """Test that the signup page loads correctly."""
        page.goto(f"{BASE_URL}/signup")

        # Check page title
        expect(page).to_have_title(re.compile("Sign up", re.IGNORECASE))

        # Check form elements exist (target main page form, not header modal)
        form = page.locator(".auth-page #signup-form")
        expect(form.locator("#email")).to_be_visible()
        expect(form.locator("#password")).to_be_visible()
        expect(form.locator("#password-confirm")).to_be_visible()
        expect(form.locator("button[type='submit']")).to_be_visible()

    def test_signup_successful_with_js(self, page: Page):
        """Test successful signup with JavaScript enabled (AJAX flow)."""
        page.goto(f"{BASE_URL}/signup")

        test_email = generate_test_email()
        test_password = "TestPass123!"

        # Fill out the form (target main page form)
        form = page.locator(".auth-page #signup-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill(test_password)
        form.locator("#password-confirm").fill(test_password)

        # Submit the form
        form.locator("button[type='submit']").click()

        # Should redirect to /playground after successful signup
        page.wait_for_url(re.compile(r"/playground"), timeout=10000)

        # Verify we're on the playground page
        expect(page).to_have_url(re.compile(r"/playground"))

    def test_signup_sets_session_cookie(self, page: Page):
        """Test that signup sets the session_secret cookie."""
        page.goto(f"{BASE_URL}/signup")

        test_email = generate_test_email()
        test_password = "TestPass123!"

        # Fill and submit
        form = page.locator(".auth-page #signup-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill(test_password)
        form.locator("#password-confirm").fill(test_password)
        form.locator("button[type='submit']").click()

        # Wait for redirect
        page.wait_for_url(re.compile(r"/playground"), timeout=10000)

        # Check for session cookie
        cookies = page.context.cookies()
        session_cookie = next((c for c in cookies if c["name"] == "session_secret"), None)
        assert session_cookie is not None, "session_secret cookie should be set"
        assert len(session_cookie["value"]) > 0, "session_secret should have a value"

    def test_signup_existing_email_auto_login(self, page: Page):
        """Test that signing up with existing email auto-logs in the user."""
        test_email = generate_test_email()
        test_password = "TestPass123!"

        # First signup
        page.goto(f"{BASE_URL}/signup")
        form = page.locator(".auth-page #signup-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill(test_password)
        form.locator("#password-confirm").fill(test_password)
        form.locator("button[type='submit']").click()
        page.wait_for_url(re.compile(r"/playground"), timeout=10000)

        # Clear cookies and try again with same email (should auto-login)
        page.context.clear_cookies()
        page.goto(f"{BASE_URL}/signup")
        form = page.locator(".auth-page #signup-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill(test_password)
        form.locator("#password-confirm").fill(test_password)
        form.locator("button[type='submit']").click()

        # Should redirect to playground (auto-login)
        page.wait_for_url(re.compile(r"/playground"), timeout=10000)

        # Verify session cookie is set
        cookies = page.context.cookies()
        assert any(c["name"] == "session_secret" for c in cookies)

    def test_signup_wrong_password_existing_user(self, page: Page):
        """Test that signup with wrong password for existing user doesn't succeed."""
        test_email = generate_test_email()
        test_password = "TestPass123!"

        # First signup
        page.goto(f"{BASE_URL}/signup")
        form = page.locator(".auth-page #signup-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill(test_password)
        form.locator("#password-confirm").fill(test_password)
        form.locator("button[type='submit']").click()
        page.wait_for_url(re.compile(r"/playground"), timeout=10000)

        # Clear cookies and try with wrong password
        page.context.clear_cookies()
        page.goto(f"{BASE_URL}/signup")
        form = page.locator(".auth-page #signup-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill("WrongPassword!")
        form.locator("#password-confirm").fill("WrongPassword!")
        form.locator("button[type='submit']").click()

        # Should stay on signup page (not redirect to playground)
        page.wait_for_timeout(3000)
        expect(page).to_have_url(re.compile(r"/signup"))


class TestLoginE2E:
    """E2E tests for the login flow."""

    def test_login_page_loads(self, page: Page):
        """Test that the login page loads correctly."""
        page.goto(f"{BASE_URL}/login")

        # Check form elements exist
        form = page.locator(".auth-page #login-form")
        expect(form.locator("#email")).to_be_visible()
        expect(form.locator("#password")).to_be_visible()
        expect(form.locator("button[type='submit']")).to_be_visible()

    def test_login_successful(self, page: Page):
        """Test successful login after signup."""
        test_email = generate_test_email()
        test_password = "TestPass123!"

        # First, create an account
        page.goto(f"{BASE_URL}/signup")
        form = page.locator(".auth-page #signup-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill(test_password)
        form.locator("#password-confirm").fill(test_password)
        form.locator("button[type='submit']").click()
        page.wait_for_url(re.compile(r"/playground"), timeout=10000)

        # Clear cookies to simulate logged out state
        page.context.clear_cookies()

        # Now login
        page.goto(f"{BASE_URL}/login")
        form = page.locator(".auth-page #login-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill(test_password)
        form.locator("button[type='submit']").click()

        # Should redirect after login
        page.wait_for_url(re.compile(r"/(playground|$)"), timeout=10000)

        # Check session cookie is set
        cookies = page.context.cookies()
        session_cookie = next((c for c in cookies if c["name"] == "session_secret"), None)
        assert session_cookie is not None, "session_secret cookie should be set after login"

    def test_login_creates_account_if_not_exists(self, page: Page):
        """Test that login auto-creates account if email doesn't exist."""
        page.goto(f"{BASE_URL}/login")

        # Login with new email (should auto-create account)
        test_email = generate_test_email()
        form = page.locator(".auth-page #login-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill("TestPass123!")
        form.locator("button[type='submit']").click()

        # Should redirect after auto-creating account
        page.wait_for_url(re.compile(r"/(playground|$)"), timeout=10000)

        # Check session cookie is set
        cookies = page.context.cookies()
        session_cookie = next((c for c in cookies if c["name"] == "session_secret"), None)
        assert session_cookie is not None, "session_secret cookie should be set"


class TestAuthFlowE2E:
    """E2E tests for complete authentication flows."""

    def test_full_signup_login_flow(self, page: Page):
        """Test complete flow: signup -> logout -> login."""
        test_email = generate_test_email()
        test_password = "TestPass123!"

        # Step 1: Signup
        page.goto(f"{BASE_URL}/signup")
        form = page.locator(".auth-page #signup-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill(test_password)
        form.locator("#password-confirm").fill(test_password)
        form.locator("button[type='submit']").click()
        page.wait_for_url(re.compile(r"/playground"), timeout=10000)

        # Verify logged in (session cookie exists)
        cookies = page.context.cookies()
        assert any(c["name"] == "session_secret" for c in cookies)

        # Step 2: Clear session (simulate logout)
        page.context.clear_cookies()

        # Step 3: Login
        page.goto(f"{BASE_URL}/login")
        form = page.locator(".auth-page #login-form")
        form.locator("#email").fill(test_email)
        form.locator("#password").fill(test_password)
        form.locator("button[type='submit']").click()

        # Should be redirected and logged in
        page.wait_for_url(re.compile(r"/(playground|$)"), timeout=10000)
        cookies = page.context.cookies()
        assert any(c["name"] == "session_secret" for c in cookies)

    def test_signup_link_from_login(self, page: Page):
        """Test that signup link on login page works."""
        page.goto(f"{BASE_URL}/login")

        # Click the signup link
        page.locator(".auth-footer a[href='/signup']").click()

        # Should be on signup page
        expect(page).to_have_url(re.compile(r"/signup"))

    def test_login_link_from_signup(self, page: Page):
        """Test that login link on signup page works."""
        page.goto(f"{BASE_URL}/signup")

        # Click the login link
        page.locator(".auth-footer a[href='/login']").click()

        # Should be on login page
        expect(page).to_have_url(re.compile(r"/login"))
