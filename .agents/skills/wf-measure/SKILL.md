---
name: wf-measure
description: Write or revise the measurements of the active milestone or probe, what was measured, how, and what came out, in the box's development workflow. Use only when the user invokes /wf-measure.
disable-model-invocation: true
argument-hint: '[results to record, or what to change]'
---

# /wf-measure: the measurements

The write-up of a milestone or a probe: what was measured, how, and what came out. This is the
point of both, so a stage without results cannot be approved.

## Before anything

Run `bin/wf status --expect measure`. If it fails, stop and tell the user what it said.

For a milestone, read the entry's `plan.md`, above all its "What it must measure". For a probe,
which has no plan, read the ledger rows it sets out to close, their "How we close it", and the
sources they cite.

## Writing a milestone's measurements

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

- Report the distribution, not just the mean: p50, p99 and the maximum, at least, for timing.
- A pass mark that was missed is reported as missed. If that makes the plan wrong, suggest
  `/wf-reopen plan <reason>`.

## Writing a probe's measurements

A probe is a record of learning the hardware as much as of the answer. The user is new to hardware
work and reads these later to see what they did and what they learned, so write it for them.
Read `.agents/reference/learner.md` first, pitch the explanations to it, and before the stage is
approved add what this probe showed about what they know and what is still new to them.

```markdown
---
summary: <one sentence: the question and its answer>
---

## What I set out to check

The ledger rows (by number, linked) and why they matter to the next milestone.

## What I did

Step by step: the setup, the wiring, the instruments and their settings, the commands and their
output, the firmware and kernel versions. Quote any script in full. Include what went wrong and
was retried: a probe that found nothing on the first try teaches the most.

## Results

What was seen, with units and the number of tries. Raw output pasted, or where the raw data is.

## What I learned

The answer in plain terms, what surprised, the hardware lesson behind it (why the pin was quiet,
what the scope trace says about the edge), and what to watch for next time.

## What it closes

Each ledger row, its new status, and anything the probe opened instead.
```

- The user does the work at the bench and you help write it up. Ask for what you need: the exact
  output, a photo, what they tried. Never fill in a step or a reading they did not report.
- **What I learned** is the point of the entry. Draft it from what they reported, explain the
  hardware behind it, and ask them to correct it in their own words.
- An answer that came out OPEN or surprising is still a result: say so, and add any new question
  to the ledger.

## For both

- **Every number comes from a run.** Never estimate one, and never present a third party's figure
  as ours. Say where the raw data is.
- Mark each ledger question this closes as MEASURED, with a link to this document.

Commit each revision. When it is right, reply that `/wf-approve` moves to publishing. Never approve
yourself.
