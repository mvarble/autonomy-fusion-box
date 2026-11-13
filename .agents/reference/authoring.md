# Writing the box's documents

How the documents in `site/content/` are written: where each kind goes, its frontmatter, links,
prose, and how mathematics, statements, citations and code are written. `site/README.md` covers
the same ground for a person editing the site; this file is what an agent follows.

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

## Frontmatter

```yaml
---
title: Allan variance
summary: How a sensor's noise changes with the time it is averaged over. # one plain sentence
depends_on: [archive/m2-allan/measure]
katex_macros:
  '\avar': '\sigma^2_A'
---
```

- `title` may contain inline math. An entry's documents default to their stage's name
  ("Writeup", "Plan"), which is usually right.
- `summary` is shown in lists, the sidebar, previews and `llms.txt`. Without it, the first
  paragraph stands in, so either write one or make the first paragraph a good summary.
- `depends_on` lists what a reader must understand first: a bare slug is a math note, anything
  else a key (`system/time-base`, `archive/m2-allan/measure`). These are the solid arrows of the map on
  the Mathematics page, so list real prerequisites, not everything mentioned.
- A page also needs `order`, its place in its track.
- An entry's `index.md` lists the `pages` it changed (written at `publish`) and the entries it
  `revises` (given to `wf start`).

## Links

- Write links the way the files sit on disk: `[Allan variance](../../math/allan-variance/)`,
  `[the plan](plan.md)`, `[the system](../../system/)`. The build rewrites them to the site's URLs
  and reports a link to a document that does not exist.
- A section's anchor is its heading in lowercase, with `$` removed and every run of characters
  other than `a`–`z` and digits turned into one hyphen: `## Fubini's theorem` is
  `#fubini-s-theorem`. Anchors are not checked, so work them out from the heading as written.
- Never put a link inside a heading.

## Prose

Write in complete sentences and paragraphs, in the register of a textbook, with tables and lists
only where they genuinely help. In `site/content/`, put each sentence on its own line and never
wrap a long one: a paragraph is its sentences, one per line, and a list item's later sentences are
indented to its text. Diffs then show which sentence changed. Never refer to the conversation that produced a document: it is
read later, by someone who was not there. Prefer a concrete example to an abstract definition
alone. Name things the way the code names them, in backticks; generics such as `Q<B, M>` must be
in backticks anyway, since `<` and `{` are Svelte syntax outside code and math.

## Mathematics

Inline math is `$x + y$`. A displayed equation opens with `$$` alone on a line, has its body
indented by one tab, and closes with `$$` alone on a line:

```
$$
	\sigma^2(\tau) = \tfrac{1}{2} \E[(\bar y_{k+1} - \bar y_k)^2] @tag(allan)
$$
```

Never write `$$f(x) = 0$$` on one line, and never use `\[ ... \]`. The site-wide macros are in
`site/katex.config.ts` (`\bbR`, `\calI`, `\bfx`, `\defeq`, `\R`, `\E`, ...); notation for
one document goes in its `katex_macros`.

Number only the equations the text refers back to, with `@tag(slug)` at the end of the last line,
and refer to them as `[](eq:slug)`, which renders as "(1)". From another document:
`[](eq:math/<slug>/<eq>)` or `[](eq:archive/<entry>/<document>/<eq>)`.

## Statements and proofs

A definition, theorem or lemma that the text states formally and returns to is a statement: a
short document of its own in a `statements/` folder beside the document that shows it.

```yaml
---
type: statement
kind: lemma # theorem, proposition, corollary, definition, remark, example
title: Whitening # optional
---
```

Its body is the statement alone. The document must be `.svx` to show it:

```svelte
<script>
	import Statement from '$lib/components/Statement.svelte';
	import Proof from '$lib/components/Proof.svelte';
	import * as whitening from './statements/whitening.md';
</script>

<Statement {...whitening} />

<Proof>

The covariance of $L^{-1} \varepsilon$ is $L^{-1} L L^\top L^{-\top} = I$.

</Proof>
```

Statements and equations share one count within a document. Refer to one as
`[%full](statement:whitening)` ("Lemma 2"). Never number or italicise a statement by hand.

## Citations

Entries go in `site/content/references.bib`, keyed `<surname><year>`. `[](cite:absil2008)` renders
as `[Absi08]`, and `[Section 4.1](cite:absil2008)` as `[Absi08, Section 4.1]`; each page ends with
exactly what it cites. Cite only sources you are certain of, with their real details: leave a
citation out rather than guess one.

## Callouts

GitHub-style blockquotes, with an optional title after the marker:

```
> [!DECISION] Why conditioning belongs to the query
> ...
```

`NOTE`, `TIP`, `WARNING`, `DECISION`, `TODO`. A `[!TODO]` is an open question: `wf approve`
refuses a document that still has one, so a draft carries its open questions as `[!TODO]`s until
they are answered. A page's `[!DECISION]` says briefly why something is the way it is and links
to the archive entry that decided it.

## Code

- **Pages quote real code.** A fence whose only line is `{path}` or `{path:start..end}` is
  replaced by those lines of the file (1-indexed, inclusive), with a caption linking to GitHub.
  Paths are relative to the document. Quoting doc comments renders them as Markdown.
- **Archive documents never quote with `{path}`.** The quote is re-read at every build, so it
  would change as the code does, and a line range would eventually break the build. Sketch the
  code inline, and when an existing interface matters, paste the lines and name the file and the
  commit they were read at.
- Sketches are compile-plausible and show signatures and types rather than bodies, unless the
  body is the point.

## Figures

A graph (a timing chain, a wiring diagram, a factor graph) is drawn with `<ModelGraph spec={name} />` from a
`*.graph.ts` file beside the document (see `site/README.md`). Any other figure is an image or a Svelte component in the
document's folder, referenced relatively. An image is imported in the document's `<script>`
(`import board from './board.jpg'`), so the build serves it under the site's base path, and placed
with `<ImageFigure src={board} alt="…" width={…} height={…}>caption</ImageFigure>`
(`$lib/components/ImageFigure.svelte`), which opens it enlarged when clicked.

Photos and screenshots are evidence, and often the raw record of a run. Copy them into the
document's folder: a phone photo converted to JPEG (`magick in.heic -auto-orient -strip -resize
1600x1600\> -quality 82 out.jpg`), a screenshot kept as PNG and stripped too. `-strip` matters: a
phone photo carries the place it was taken. Write alt text that says what the image shows, readings
included, for a reader who cannot see it, and a caption that says why it is there. Describe only what
is legible; ask the user about anything that is not.
