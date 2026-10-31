---
name: wf-measure
description: Write or revise the measurements of the active milestone, the numbers it set out to produce and how they were taken, in the box's development workflow. Use only when the user invokes /wf-measure.
disable-model-invocation: true
argument-hint: '[results to record, or what to change]'
---

# /wf-measure: the measurements

The milestone's write-up: what was measured, how, and what came out. This is the point of a
milestone, so a stage without numbers cannot be approved.

## Before anything

Run `bin/wf status --expect measure`. If it fails, stop and tell the user what it said.

Read the entry's `plan.md`, above all its "What it must measure".

## Writing

`site/content/archive/<slug>/measure.md`:

```markdown
---
summary: <one sentence, with the headline number>
---

## Method

The setup, the instruments and their own errors, the firmware and kernel versions, and the
conditions: enough for someone to repeat it.

## Results

Tables and figures of what was measured, each number with its units and its sample size.

## What this means

Against the plan's pass marks: what passed, what did not, and what it changes.
```

- **Every number comes from a run.** Never estimate one, and never present a third party's figure
  as ours. Say where the raw data is.
- Report the distribution, not just the mean: p50, p99 and the maximum, at least, for timing.
- A pass mark that was missed is reported as missed. If that makes the plan wrong, suggest
  `/wf-reopen plan <reason>`.
- Mark each ledger question this closes as MEASURED, with a link to this document.

Commit each revision. When it is right, reply that `/wf-approve` moves to publishing. Never approve
yourself.
