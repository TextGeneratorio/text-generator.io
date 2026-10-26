---
name: code-review
description: Review code for bugs, security issues, performance, and best practices.
category: development
version: 1.0.0
author: text-generator.io
---

# Code Review

Perform thorough code review on submitted code.

## Procedure

1. **Security**: Check for injection vulnerabilities, hardcoded secrets, unsafe operations
2. **Bugs**: Look for null/undefined errors, off-by-one, race conditions, resource leaks
3. **Performance**: Identify N+1 queries, unnecessary allocations, missing indexes
4. **Style**: Check naming conventions, dead code, overly complex logic
5. **Architecture**: Evaluate separation of concerns, testability, error handling

## Output Format

For each finding:
- **Severity**: Critical / Warning / Suggestion
- **Line**: Where the issue is
- **Issue**: What's wrong
- **Fix**: How to fix it

End with a summary: overall quality score (1-10) and top 3 priorities.
