# The box's plan

What `/wf-plan` asks of the box besides what the skill says.

The plan is where design happens for a milestone: if a choice is expensive to reverse, it belongs
in a decision entry first, not buried in a task.

**Before writing.** Read the [ledger](../../../site/content/reference/open-questions/index.md) and
the milestone's section of `site/content/reference/milestones/index.md`. For a milestone with
hardware work, read `.agents/reference/learner.md` too, and give a step the user has not done before
enough detail to do at the bench.

**The template.**

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

- A task that touches the Pi's boot config or writes F9R flash says so plainly, and is shown to the
  user as a diff before it is run.
- Name which ledger questions the plan rests on, and which it will close.
