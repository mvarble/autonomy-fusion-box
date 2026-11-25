// The one place that defines the site's structure. `docsSite()` hands the tracks and the entry
// documents to the content database, and the pages `@mvarble/mesearch-workflow` shares read this
// module as `$site`, with defaults for what it leaves out: the stages of each kind, for instance,
// come from `workflow.config.ts`.

export const SITE = {
    name: 'fusion box',
    tagline: 'GNSS, IMU and camera on one GPS-disciplined timebase, with the numbers to prove it.',
    description:
        'A portable, battery-powered box that records GNSS, IMU and camera data on one ' +
        'GPS-disciplined timebase, and the record of how it was decided, built and measured.',
    repo: 'https://github.com/mvarble/autonomy-fusion-box',
    branch: 'main',
    version: '0.0.0',
} as const;

export interface Track {
    id: string;
    title: string;
    /** A short label for the top bar. */
    short: string;
    blurb: string;
}

// The tracks of pages, in reading order. A page belongs to the track named by its folder under
// `content/`, and is placed within it by its `order` frontmatter. Pages say what the box *is*: they
// are rewritten as it changes, and what they used to say lives on in the archive.
export const TRACKS: Track[] = [
    {
        id: 'start',
        title: 'Start here',
        short: 'Start',
        blurb: 'What the box is.',
    },
    {
        id: 'system',
        title: 'The system',
        short: 'System',
        blurb: 'How the box works as built: its time base, sensors, software and power.',
    },
    {
        id: 'reference',
        title: 'Reference',
        short: 'Reference',
        blurb: 'How the work is done, the milestones, and the ledger of what is still unverified.',
    },
];

// The two collections beside the tracks.
export const MATH = {
    id: 'math',
    title: 'Mathematics',
    short: 'Math',
    blurb:
        'The mathematics the box rests on, one idea to a note, linked by what each builds on: ' +
        'Allan variance, preintegration, and whatever else earns a note.',
};

export const ARCHIVE = {
    id: 'archive',
    title: 'Archive',
    short: 'Archive',
    blurb:
        'How each part of the box came to be: the decisions argued for it, the plans it was built ' +
        'by, and the numbers it measured, kept as they were approved.',
    // The paragraph the archive's page opens with.
    about:
        'An entry is opened for each piece of work and moves through its stages: for a milestone, ' +
        'the plan, the build, the measurements, and last the pages that say what the milestone ' +
        'made true. Between milestones, a probe records one session at the bench: what was done, ' +
        'what was seen, what it taught, and the open questions it closed. What each stage ' +
        'approved is kept here as it was approved. When the box later changes, a new entry ' +
        'revises the old one rather than rewriting it.',
};

// What `llms.txt` says of the pages, after "Every document below links to its Markdown source."
export const LLMS = {
    about:
        'The pages say what the box is now; the Archive keeps how each part came to be, and may ' +
        'describe what has since changed.',
};

// The documents an archive entry may hold, in the order they are written.
export const DOCUMENTS = [
    { name: 'writeup', title: 'Writeup' },
    { name: 'plan', title: 'Plan' },
    { name: 'measure', title: 'Measurements' },
] as const;

export const KIND_LABELS: Record<string, string> = {
    milestone: 'Milestone',
    probe: 'Probe',
    decision: 'Decision',
    chore: 'Chore',
};

export const STATUS_LABELS: Record<string, string> = {
    active: 'In progress',
    done: 'Done',
    abandoned: 'Abandoned',
};
