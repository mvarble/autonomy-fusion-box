# Writing the box's documents

The box's own conventions for the documents in `site/content/`, over the ones every project
documented this way shares: `.agents/reference/mesearch/authoring.md` (what each kind of writing
promises, frontmatter, links, prose, callouts, code and figures) and `markup.md` beside it
(mathematics, numbered equations, statements and citations). Where they differ, this file wins.
`site/README.md` covers the same ground for a person editing the site.

## What the site is for

The site is the set of lab notebooks from the user's attempt to learn embedded work hands on, with
an AI assistant at their side. They trained as a mathematician and work as a navigation engineer;
the box is their first embedded project, and `.agents/reference/learner.md` says where they stand.
The site is honest about that, and the writing follows from it:

- **First person for the bench.** Archive documents say "I" for what the user did and saw. The
  assistant helps plan, explain and write; the wiring, the bench work and the readings are theirs.
- **Teach as well as record.** A reader new to the hardware should be able to follow an entry and
  do it again. Explain an embedded idea the first time it matters (a baud rate, IOREF, a UBX frame),
  briefly, at the point it is needed; skip what an estimation engineer already knows.
- **Write what should be done, not the order it happened in.** When the user's experiments were
  scattered, lay them out as the steps someone should follow, and leave the detours out unless they
  teach something.
- **Only what was reported or seen.** Every reading, setting and step comes from the user, a file,
  a screenshot or a document. Say plainly what is not known (when a log was recorded, what a setting
  does) rather than fill it in, and never present something recalled from memory as fact: cite it,
  or leave it out.

## Where things go

```
site/content/
    landing.md                          the home page's prose
    <track>/<slug>/index.md             a page: start, system, reference
    reference/open-questions/index.md   the ledger of unverified facts, always open
    math/<slug>/index.md                a math note
    archive/<slug>/index.md             an entry, opened by `bin/wf start`
    archive/<slug>/writeup.md           its documents, one per stage that has one
    archive/<slug>/plan.md
    archive/<slug>/measure.md
    references.bib                      the bibliography
```

The three kinds of writing differ in what they promise the reader.

- **Pages say what is.** They describe the box as it stands, quote the code and config that exist,
  and report measured numbers with a link to where they were measured. They change at an entry's
  `publish` stage.
- **Math notes say what is true**, independently of the box: one idea to a note (Allan variance,
  IMU preintegration), at enough length to be worth reading alone.
- **Archive documents discuss what may be.** They argue, weigh alternatives and leave room for
  doubt, as they stood when approved. Once approved they are frozen: they may drift from the box,
  and that is what they are for.

Before writing about an idea, search for it: `grep -rni 'allan' site/content/`. If the site
explains it, link there. If a writeup needs an idea the site does not have, explain it in a
section of the writeup; promote it to a math note only when it stands alone and takes several
sections, or when a second document needs it.

## Prose

In `site/content/`, put each sentence on its own line and never wrap a long one: a paragraph is its
sentences, one per line, and a list item's later sentences are indented to its text. Diffs then show
which sentence changed.

## Figures

A graph here is a timing chain, a wiring diagram or a factor graph, drawn with `<ModelGraph>`.

Photos and screenshots are evidence, and often the raw record of a run. Copy them into the
document's folder: a phone photo converted to JPEG (`magick in.heic -auto-orient -strip -resize
1600x1600\> -quality 82 out.jpg`), a screenshot kept as PNG and stripped too. `-strip` matters: a
phone photo carries the place it was taken. Write alt text that says what the image shows, readings
included, for a reader who cannot see it, and a caption that says why it is there. Describe only what
is legible; ask the user about anything that is not.
