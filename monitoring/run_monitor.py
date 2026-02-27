#!/usr/bin/env python3
"""
Monitor Runner

Runs E2E tests on a schedule and triggers Claude agent for fixes.

Usage:
    # Run once
    python monitoring/run_monitor.py

    # Run continuously (every hour)
    python monitoring/run_monitor.py --daemon --interval 3600

    # Run with auto-fix enabled
    python monitoring/run_monitor.py --auto-fix
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configure logging
LOG_DIR = Path("/nvme0n1-disk/code/text-generator.io/monitoring/logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "monitor.log"),
    ],
)
logger = logging.getLogger(__name__)


def run_e2e_test(auto_fix: bool = False) -> dict:
    """Run the E2E auth flow test."""
    logger.info("Running E2E auth flow test...")

    cmd = [
        sys.executable,
        "/nvme0n1-disk/code/text-generator.io/monitoring/e2e_auth_flow.py",
        "--json",
    ]

    if auto_fix:
        cmd.append("--auto-fix")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/nvme0n1-disk/code/text-generator.io",
        )

        # Parse JSON output
        try:
            summary = json.loads(result.stdout)
        except json.JSONDecodeError:
            summary = {
                "success": result.returncode == 0,
                "error": "Failed to parse test output",
                "stdout": result.stdout[:1000],
                "stderr": result.stderr[:1000],
            }

        # Log results
        log_file = LOG_DIR / f"e2e_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, "w") as f:
            json.dump(summary, f, indent=2)

        return summary

    except subprocess.TimeoutExpired:
        logger.error("E2E test timed out")
        return {"success": False, "error": "Test timed out"}
    except Exception as e:
        logger.error(f"Error running E2E test: {e}")
        return {"success": False, "error": str(e)}


def trigger_claude_fix(summary: dict):
    """Trigger Claude agent to fix issues."""
    logger.info("Triggering Claude agent to investigate and fix...")

    # Build error context
    if "results" in summary:
        failed_steps = [r for r in summary["results"] if not r.get("success")]
        error_context = "\n".join([f"- {r['step']}: {r.get('details', 'No details')}" for r in failed_steps])
    else:
        error_context = summary.get("error", "Unknown error")

    prompt = f"""The E2E auth flow monitoring test failed. Please investigate and fix.

Failed steps:
{error_context}

Steps to investigate:
1. Check supervisor logs: sudo supervisorctl tail -500 text-generator-site
2. Look for errors in main.py auth endpoints (/api/signup, /api/login, /api/logout, /api/current-user, /api/get-user/stripe-usage, /api/delete-account)
3. Fix any issues found
4. Restart the service: sudo supervisorctl restart text-generator-site

After fixing, the next monitor run will verify the fix.
"""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            cwd="/nvme0n1-disk/code/text-generator.io",
            capture_output=True,
            text=True,
            timeout=300,
        )
        logger.info(f"Claude agent completed with return code: {result.returncode}")
        if result.stdout:
            logger.info(f"Claude output:\n{result.stdout[:2000]}")
    except subprocess.TimeoutExpired:
        logger.error("Claude agent timed out")
    except FileNotFoundError:
        logger.warning("Claude CLI not found - skipping auto-fix")
    except Exception as e:
        logger.error(f"Error running Claude agent: {e}")


def cleanup_old_logs(max_age_days: int = 7):
    """Clean up log files older than max_age_days."""
    cutoff = time.time() - (max_age_days * 86400)
    for log_file in LOG_DIR.glob("e2e_*.json"):
        if log_file.stat().st_mtime < cutoff:
            log_file.unlink()
            logger.debug(f"Deleted old log: {log_file}")


def main():
    parser = argparse.ArgumentParser(description="Monitor Runner")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=3600, help="Interval between runs in seconds (default: 3600)")
    parser.add_argument("--auto-fix", action="store_true", help="Trigger Claude agent to fix issues")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("E2E Monitor Starting")
    logger.info(f"Auto-fix: {args.auto_fix}")
    logger.info(f"Daemon mode: {args.daemon}")
    logger.info("=" * 50)

    consecutive_failures = 0
    max_consecutive_failures = 3  # Trigger auto-fix after this many failures

    while True:
        try:
            # Clean up old logs
            cleanup_old_logs()

            # Run the test
            summary = run_e2e_test(auto_fix=False)  # Don't auto-fix in the test itself

            if summary.get("success"):
                logger.info("E2E test PASSED")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                logger.error(f"E2E test FAILED (consecutive failures: {consecutive_failures})")

                # Trigger auto-fix if enabled and we've had multiple failures
                if args.auto_fix and consecutive_failures >= max_consecutive_failures:
                    logger.info(f"Triggering auto-fix after {consecutive_failures} consecutive failures")
                    trigger_claude_fix(summary)
                    consecutive_failures = 0  # Reset counter after attempting fix

        except Exception as e:
            logger.error(f"Monitor error: {e}")
            consecutive_failures += 1

        if not args.daemon:
            break

        logger.info(f"Sleeping for {args.interval} seconds...")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
