---
name: extract-learnings
description: [DEPRECATED] Esta skill ha sido deprecada. Es una actividad post-mortem esporádica, no una skill operativa recurrente. Se mantiene solo como referencia histórica de housekeeping interno.
---

# Extract Learnings

Only record what a future session would genuinely benefit from - a gotcha, a non-obvious fix, or a durable preference. If the task was routine, do nothing.

Where each learning goes:
- Short fact or preference useful every session -> Assistant Notes, via edit_assistant_notes
- Detail useful only sometimes -> a file under /mnt/notes/assistant-notes/, via edit_assistant_notes (never run_shell)
- A repeatable multi-step workflow -> a new skill (see below)

## Writing a skill

Create /mnt/skills/<kebab-name>/SKILL.md via run_shell, starting with this front matter:

---
name: <kebab-name>
description: Use when <trigger>. 1-2 sentences, <=50 words - it shows in the always-loaded skill list.
---

Then the body: steps and gotchas, enough to repeat the workflow. Only front matter is shown in future prompts; the body loads when you read the file. Prefer updating an existing note or skill over a near-duplicate.

Match the above format exactly (first four characters must be three dashes and a newline).