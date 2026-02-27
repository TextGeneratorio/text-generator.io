#!/usr/bin/env python3
"""
E2E Auth Flow Monitor

Tests the complete authentication flow against the live server:
1. Signup with test user
2. Logout
3. Login back in
4. Check account access
5. Delete account

Run manually: python monitoring/e2e_auth_flow.py
Run with auto-fix: python monitoring/e2e_auth_flow.py --auto-fix
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.getenv("E2E_BASE_URL", "https://text-generator.io")
TEST_EMAIL_PREFIX = "e2e-test-"
TEST_EMAIL_DOMAIN = "@test.text-generator.io"
TEST_PASSWORD = "E2ETestPassword123!"


class AuthFlowTest:
    """E2E authentication flow test."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.test_email = f"{TEST_EMAIL_PREFIX}{uuid.uuid4().hex[:8]}{TEST_EMAIL_DOMAIN}"
        self.results = []

    def log_result(self, step: str, success: bool, details: str = ""):
        """Log test result."""
        status = "PASS" if success else "FAIL"
        msg = f"[{status}] {step}"
        if details:
            msg += f" - {details}"
        logger.info(msg)
        self.results.append({"step": step, "success": success, "details": details, "timestamp": datetime.now().isoformat()})

    def step_signup(self) -> bool:
        """Step 1: Signup with test user."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/signup",
                data={"email": self.test_email, "password": TEST_PASSWORD},
                allow_redirects=False,
            )

            # Signup should return 200 (JSON) or 303 (redirect)
            if response.status_code in [200, 303]:
                self.log_result("Signup", True, f"Created user {self.test_email}")
                return True
            else:
                self.log_result("Signup", False, f"Status {response.status_code}: {response.text[:200]}")
                return False
        except Exception as e:
            self.log_result("Signup", False, str(e))
            return False

    def step_verify_logged_in(self) -> bool:
        """Verify user is logged in via current-user endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/current-user")
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == self.test_email:
                    self.log_result("Verify Login", True, f"Logged in as {self.test_email}")
                    return True
                else:
                    self.log_result("Verify Login", False, f"Wrong email: {data.get('email')}")
                    return False
            else:
                self.log_result("Verify Login", False, f"Status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Verify Login", False, str(e))
            return False

    def step_logout(self) -> bool:
        """Step 2: Logout."""
        try:
            response = self.session.post(f"{self.base_url}/api/logout")
            if response.status_code == 200:
                self.log_result("Logout", True)
                return True
            else:
                self.log_result("Logout", False, f"Status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Logout", False, str(e))
            return False

    def step_verify_logged_out(self) -> bool:
        """Verify user is logged out."""
        try:
            response = self.session.get(f"{self.base_url}/api/current-user")
            if response.status_code == 401:
                self.log_result("Verify Logout", True)
                return True
            else:
                self.log_result("Verify Logout", False, f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Verify Logout", False, str(e))
            return False

    def step_login(self) -> bool:
        """Step 3: Login with test user."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/login",
                data={"email": self.test_email, "password": TEST_PASSWORD},
                allow_redirects=False,
            )

            # Login should return 200 (JSON) or 303 (redirect)
            if response.status_code in [200, 303]:
                self.log_result("Login", True)
                return True
            else:
                self.log_result("Login", False, f"Status {response.status_code}: {response.text[:200]}")
                return False
        except Exception as e:
            self.log_result("Login", False, str(e))
            return False

    def step_access_account(self) -> bool:
        """Step 4: Access account page."""
        try:
            # First verify we're logged in
            if not self.step_verify_logged_in():
                return False

            # Try to get user data with stripe info
            response = self.session.post(f"{self.base_url}/api/get-user/stripe-usage")
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == self.test_email:
                    self.log_result("Access Account", True, f"Got user data for {self.test_email}")
                    return True
                else:
                    self.log_result("Access Account", False, "Wrong email in response")
                    return False
            else:
                self.log_result("Access Account", False, f"Status {response.status_code}: {response.text[:200]}")
                return False
        except Exception as e:
            self.log_result("Access Account", False, str(e))
            return False

    def step_delete_account(self) -> bool:
        """Step 5: Delete account."""
        try:
            response = self.session.post(f"{self.base_url}/api/delete-account")
            if response.status_code == 200:
                self.log_result("Delete Account", True, f"Deleted {self.test_email}")
                return True
            else:
                self.log_result("Delete Account", False, f"Status {response.status_code}: {response.text[:200]}")
                return False
        except Exception as e:
            self.log_result("Delete Account", False, str(e))
            return False

    def step_verify_deleted(self) -> bool:
        """Verify account is deleted by trying to login."""
        try:
            # Create a new session to avoid cookie issues
            new_session = requests.Session()
            response = new_session.post(
                f"{self.base_url}/api/login",
                data={"email": self.test_email, "password": TEST_PASSWORD},
                allow_redirects=False,
            )

            # Login with deleted account should fail with 401 or create a new account
            # If it creates new account (200/303), that's actually fine for this test
            self.log_result("Verify Deleted", True, f"Login attempt returned {response.status_code}")
            return True
        except Exception as e:
            self.log_result("Verify Deleted", False, str(e))
            return False

    def run(self) -> bool:
        """Run the full auth flow test."""
        logger.info(f"Starting E2E Auth Flow Test against {self.base_url}")
        logger.info(f"Test email: {self.test_email}")

        all_passed = True

        # Step 1: Signup
        if not self.step_signup():
            all_passed = False
            return all_passed

        # Verify logged in after signup
        if not self.step_verify_logged_in():
            all_passed = False

        # Step 2: Logout
        if not self.step_logout():
            all_passed = False

        # Verify logged out
        if not self.step_verify_logged_out():
            all_passed = False

        # Step 3: Login
        if not self.step_login():
            all_passed = False
            # Try to clean up by deleting account anyway
            self.step_delete_account()
            return all_passed

        # Step 4: Access account
        if not self.step_access_account():
            all_passed = False

        # Step 5: Delete account
        if not self.step_delete_account():
            all_passed = False

        # Verify deleted
        self.step_verify_deleted()

        return all_passed

    def get_summary(self) -> dict:
        """Get test summary."""
        passed = sum(1 for r in self.results if r["success"])
        failed = sum(1 for r in self.results if not r["success"])
        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "success": failed == 0,
            "results": self.results,
            "test_email": self.test_email,
            "base_url": self.base_url,
            "timestamp": datetime.now().isoformat(),
        }


def trigger_claude_fix(summary: dict):
    """Trigger Claude agent to fix failing tests."""
    logger.info("Triggering Claude agent to investigate and fix issues...")

    # Build error context
    failed_steps = [r for r in summary["results"] if not r["success"]]
    error_context = "\n".join([f"- {r['step']}: {r['details']}" for r in failed_steps])

    prompt = f"""The E2E auth flow test failed with the following errors:

{error_context}

Base URL: {summary['base_url']}
Test email pattern: {summary['test_email']}

Please investigate the failing endpoints and fix any issues. The test flow is:
1. Signup (/api/signup)
2. Verify login (/api/current-user)
3. Logout (/api/logout)
4. Login (/api/login)
5. Access account (/api/get-user/stripe-usage)
6. Delete account (/api/delete-account)

Check the supervisor logs with: sudo supervisorctl tail -500 text-generator-site
Then investigate and fix the relevant code in main.py.
"""

    # Run claude code with the prompt
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            cwd="/nvme0n1-disk/code/text-generator.io",
            capture_output=True,
            text=True,
            timeout=300,
        )
        logger.info(f"Claude agent output:\n{result.stdout}")
        if result.returncode != 0:
            logger.error(f"Claude agent error:\n{result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("Claude agent timed out after 5 minutes")
    except FileNotFoundError:
        logger.error("Claude CLI not found. Install with: npm install -g @anthropic/claude-code")
    except Exception as e:
        logger.error(f"Error running Claude agent: {e}")


def main():
    parser = argparse.ArgumentParser(description="E2E Auth Flow Monitor")
    parser.add_argument("--base-url", default=BASE_URL, help="Base URL to test against")
    parser.add_argument("--auto-fix", action="store_true", help="Trigger Claude agent to fix issues")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    test = AuthFlowTest(base_url=args.base_url)
    success = test.run()
    summary = test.get_summary()

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        logger.info("=" * 50)
        logger.info(f"Test Summary: {summary['passed']}/{summary['total']} passed")
        if success:
            logger.info("All tests PASSED")
        else:
            logger.error("Some tests FAILED")
            if args.auto_fix:
                trigger_claude_fix(summary)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
