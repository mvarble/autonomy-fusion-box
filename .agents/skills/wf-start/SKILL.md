---
name: wf-start
description: Open a new entry (a milestone, a probe, a decision or a chore) on the current branch of the box's development workflow. Use only when the user invokes /wf-start.
disable-model-invocation: true
argument-hint: '<slug> <milestone|probe|decision|chore> [what it is about] [revises <slug>]'
---

# /wf-start: open an entry

## Steps

1. Work out the slug (lowercase words joined by hyphens, named after the idea), the kind, a title,
   and any entry it revises from what the user wrote. Ask if the kind is unclear: a **milestone**
   is one row of the milestones table and ends in measured numbers; a **probe** is one session at
   the bench, written up as a lab, that usually closes questions in the ledger (a warm-up that closes
   none is a probe too) and writes no box code; a **decision** is an argued position; a **chore** is a refactor or a
   tooling change with nothing to measure.
2. If the current branch is `main`, make a branch for the entry first (`git switch -c <slug>`),
   unless your environment names the branch to work on.
3. Run `bin/wf start <slug> --kind <kind> --title "<Title>"`, adding `--revises <slug>,...` when
   it changes the story of finished entries. If it refuses, tell the user what it said and stop.
4. Replace the `[!TODO]` in `site/content/archive/<slug>/index.md` with a paragraph saying what
   the entry sets out to do and why, from what the user said. Ask for what is missing rather than
   inventing it.
5. Commit the entry folder and `.workflow/active` ("Start <slug>: <title>").
6. Reply with the first stage's skill (`bin/wf status` names it). Do not start that stage until
   the user invokes it.
