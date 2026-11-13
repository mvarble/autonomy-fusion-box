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

Read `.agents/reference/authoring.md` once per session. For a milestone, read the entry's
`plan.md`, above all its "What it must measure". For a probe, which has no plan, read the ledger
rows it sets out to close, their "How we close it", and the sources they cite; a warm-up probe may
close none.

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

A probe is a lab: a record of learning the hardware as much as of the answer, written so that
someone new to embedded work could follow it and do it again. The user reads these later to see
what they did and what they learned, and the site is honest that they are learning (see "What the
site is for" in `.agents/reference/authoring.md`). Read `.agents/reference/learner.md` first, pitch
the explanations to it, and before the stage is approved add what this probe showed about what they
know and what is still new to them.

```markdown
---
summary: <one sentence: what the lab does, and its headline result>
---

<A short opening, in the first person: what the lab sets out to do and why, and a numbered list of
its steps, each linking its section.>

## The setup

<The hardware (a photo), the instruments and tools, the host and the versions of everything.>

## 1. <A step, named for what it does>

**What it is for.** Why this step, and where it fits: in the lab, and in the box.

**How it is done.** The wiring, the settings, the commands and any script, quoted in full (in a
`<details>` block when it is long). Explain the idea behind it the first time it matters.

**What to look for.** What a good result looks like, before it is shown.

**What came out.** The screenshot, photo or pasted output, then what it shows, with every number
from the run and the number of runs.

**What I learned.** Bullets: each a lesson in bold, then the hardware behind it, linking forward to
the step that comes back to it.

## 2. …

## Results

A table of what each step checked and found, numbers included, and where the raw data is.

## What comes next

The ledger rows it closes (marked MEASURED, linked here), the ones it moves forward, and any it
opened.
```

- **Write the lab as it should be done**, not in the order things happened. Scattered experiments
  become steps someone could follow; a detour stays only if it teaches.
- `bin/wf approve` requires a `## Results` section, so keep one even when every step reports its own
  results.
- The user does the work at the bench and you help write it up. Ask for what you need: the exact
  output, a screenshot, a photo, what they tried. Never fill in a step or a reading they did not
  report, and never state as fact what you only recall: check it in a document, or say it is not
  known.
- Screenshots of a terminal or an instrument are the best raw record. Copy them into the entry's
  folder and show them with `ImageFigure`, as `authoring.md` says.
- **What I learned** is the point of each step. Draft it from what they reported, explain the
  hardware behind it, and ask them to correct it in their own words; if they have nothing to add,
  the draft stands.
- An answer that came out OPEN or surprising is still a result: say so, and add any new question
  to the ledger.

## For both

- **Every number comes from a run.** Never estimate one, and never present a third party's figure
  as ours. Say where the raw data is.
- Mark each ledger question this closes as MEASURED, with a link to this document.

Commit each revision. When it is right, reply that `/wf-approve` moves to publishing. Never approve
yourself.
