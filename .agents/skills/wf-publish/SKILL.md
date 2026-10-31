---
name: wf-publish
description: Bring the box's documentation pages up to date with what the active entry built, measured or decided, and link the entry to them; the last stage of the box's development workflow. Use only when the user invokes /wf-publish.
disable-model-invocation: true
argument-hint: '[pages to start with, or what to change]'
---

# /wf-publish: the pages

The entry is built and measured (or, for a decision, argued). Now the pages that say what the box
*is* must say it. The archive discussed what might be; the pages tell what is.

## Before anything

Run `bin/wf status --expect publish`. If it fails, stop and tell the user what it said.

Read `.agents/reference/authoring.md` once per session, the entry's documents, and the code it
added. Read the pages that are affected (`site/content/{start,system,reference}/`, the landing page)
before changing them.

## Writing

- **The system.** Add or rewrite the pages that describe what now exists, quoting the real code and
  config with `{path:start..end}` fences, and quoting measured numbers with a link to the entry's
  measurements. A choice a reader would wonder about gets a short `> [!DECISION]` linking the entry
  that made it.
- **Reference.** The milestones page, where a milestone's status changed.
- **Drop what is no longer true.** A page describes only the current box. What it replaced stays in
  the archive.
- **The entry's `index.md`.** Replace its opening paragraph with what the entry did, for a reader of
  the archive, and list every page it changed under `pages`. `wf approve` refuses a changed page
  that is not listed, and a listed one the branch did not change.

Build the site (`cd site && pnpm build`) and fix every warning and broken link. Commit as you go.

When the pages are right, run `bin/wf check` and reply that `/wf-approve` finishes the entry, after
which the branch is ready to merge. Never approve yourself.
