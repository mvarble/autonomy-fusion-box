# The box's publish

What `/wf-publish` asks of the box besides what the skill says.

The pages that say what the box _is_ are under `site/content/{start,system,reference}/`, with the
landing page. Read the affected ones before changing them.

- **The system.** Add or rewrite the pages that describe what now exists, quoting the real code and
  config with `{path:start..end}` fences, and quoting measured numbers with a link to the entry's
  measurements.
- **Reference.** The milestones page, where a milestone's status changed. For a probe, the ledger
  rows it closed are usually the only page; a probe changes a system page only if what it found
  corrects one.
- **Write as `authoring.md` says**: one sentence per line, in the site's own voice. The home page
  says what the site is for; keep it true when an entry changes that.
- **What it amends.** The references a done entry's documents make that an entry may move or remove
  are ledger rows, pages and their headings, and math notes.
