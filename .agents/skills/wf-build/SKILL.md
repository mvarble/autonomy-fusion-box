---
name: wf-build
description: Build the active entry by working through its approved plan, task by task, with a check and a commit per task, in the box's development workflow. Use only when the user invokes /wf-build.
disable-model-invocation: true
argument-hint: '[a task to start from, or a limit such as "the first three"]'
---

# /wf-build: the build

Work through `plan.md` in order: do each task, run its check, tick its box, commit.

## Before anything

Run `bin/wf status --expect build`. If it fails, stop and tell the user what it said.

Read `.agents/reference/workflow.md` once per session, the entry's `plan.md`, and the rules in
`AGENTS.md`, above all the stamping rule.

## Each task

1. Do exactly what the task says. Details it leaves open are yours to decide.
2. Run its check. A task that needs the hardware is done by the user, or with them: say what to
   run and what to expect, and do not tick the box until they report the result.
3. Tick the task's box in `plan.md`; change nothing else in the plan, since `wf check` refuses any
   other edit to it.
4. Commit, with a message saying what the task added.

Record anything the build teaches about a hardware fact in the ledger
(`site/content/reference/open-questions/index.md`), which stays open at every stage.

## When the plan is wrong

If a task cannot be done as planned, or the hardware disagrees with a document, stop. Tell the user
what was found and suggest `/wf-reopen plan <reason>`. Do not deviate quietly, and never edit an
approved document.

## At the end

When every box is ticked, run the plan's "Done when" checks and `bin/wf check`. Reply that
`/wf-approve` moves on. Never approve yourself.
