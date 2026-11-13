---
name: wf-plan
description: Write or revise the plan of the active milestone or chore, a checklist of tasks and the measurements it must end in, in the box's development workflow. Use only when the user invokes /wf-plan.
disable-model-invocation: true
argument-hint: '[what to change]'
---

# /wf-plan: the plan

What will be done, in order, and how anyone will know it worked. The plan is where design happens
for a milestone: if a choice is expensive to reverse, it belongs in a decision entry first, not
buried in a task.

## Before anything

Run `bin/wf status --expect plan`. If it fails, stop and tell the user what it said.

Read `.agents/reference/workflow.md` once per session, the entry's `index.md`, the
[ledger](../../../site/content/reference/open-questions/index.md), and the milestone's section of
`site/content/reference/milestones/index.md`. For a milestone with hardware work, read
`.agents/reference/learner.md` too, and give a step the user has not done before enough detail to
do at the bench.

## Writing

`site/content/archive/<slug>/plan.md`:

```markdown
---
summary: <one sentence>
---

## <Group, such as preflight, wiring or firmware>

- [ ] <One task, small enough for one commit.> Check: `<how we know it worked>`.
- [ ] ...

## What it must measure

<For a milestone: the numbers the measurements stage has to report, the conditions they are
measured under, and the pass mark for each.>

## Done when

<The checks that must pass at the end.>
```

- Order the tasks so that each builds on finished ones.
- A task that touches the Pi's boot config or writes F9R flash says so plainly, and is shown to the
  user as a diff before it is run.
- Name which ledger questions the plan rests on, and which it will close.

Commit each revision. When the plan is right, reply that `/wf-approve` starts the build. Never
approve yourself.
