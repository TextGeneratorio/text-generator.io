// Shared browser-local prompt recipes. Keep the two site copies identical.
export const promptModes = [
  {
    "id": "concise",
    "label": "Token concise",
    "description": "Keep the task, reduce the chatter.",
    "instructions": "Complete the task with the smallest sufficient change. Preserve every requirement, quoted string, code block, and constraint. Avoid repeated explanations. Ask only blocking questions. Report the result, checks run, and blockers concisely."
  },
  {
    "id": "implement",
    "label": "Thorough implementation",
    "description": "Finish the work, not just a plan.",
    "instructions": "Inspect the relevant code and project instructions first. Preserve existing user changes. Implement the requested work end to end using existing patterns. Handle realistic edge cases and errors. Do not stop at a plan or leave required work as TODOs. Run relevant checks, fix failures caused by your changes, and report remaining blockers honestly."
  },
  {
    "id": "verify",
    "label": "Tests & verification",
    "description": "Require evidence, not confidence.",
    "instructions": "Implement the requested change and add focused regression tests for the changed behavior, edge cases, and failure paths. Run relevant tests, type checks, and builds; fix failures caused by your work. Report exact commands and results, separating existing failures and skipped checks. Never claim an unrun check passed."
  },
  {
    "id": "e2e",
    "label": "End-to-end QA",
    "description": "Check the real user journey.",
    "instructions": "Implement and verify the complete user journey. Add or run relevant end-to-end tests including success, validation, failure, and recovery paths. For UI work, check mobile layout, keyboard access, and browser console errors, and capture screenshots when available. Unit tests are not browser verification. Report commands, results, evidence, and any untested environment."
  },
  {
    "id": "deploy",
    "label": "Deployment readiness",
    "description": "Build, smoke test, and plan rollback.",
    "instructions": "Complete the implementation, tests, and production build. Check configuration, migrations, secrets handling, and compatibility. Prepare a reversible deployment and rollback plan. Deploy only when explicitly authorized by the task and allowed by the environment; otherwise report readiness without deploying. After an authorized deployment, smoke-test the live URL and key user flow. Report the exact version, URL, checks, and any blockers. Never claim deployment success without evidence."
  }
];

export function improvePrompt(input, mode = "implement", extra = "") {
  if (typeof input !== "string" || !input.trim()) throw new Error("Enter a prompt first.");
  if (input.length > 12000 || extra.length > 4000) throw new Error("Prompt or requirements exceed the input limit.");
  const selected = promptModes.find(item => item.id === mode);
  if (!selected) throw new Error("Choose a valid mode.");
  return `Task:\n${input.trim()}\n\nWorking requirements:\n${selected.instructions}\nPreserve the original scope and constraints; do not invent requirements. Respect project instructions, access restrictions, and approval gates. If blocked, explain what is needed rather than claiming completion.${extra.trim() ? `\n\nAdditional requirements:\n${extra.trim()}` : ""}`;
}
