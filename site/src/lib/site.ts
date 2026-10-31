// The one place that defines the site's structure. `vite.config.ts` hands the tracks and the
// entry documents to the content database, and the navigation is built from the same lists.

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
        blurb: 'What the box is, and how the work on it is done.',
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
        blurb: 'The milestones, and the ledger of what is still unverified.',
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
};

// The documents an archive entry may hold, in the order they are written.
export const DOCUMENTS = [
    { name: 'writeup', title: 'Writeup' },
    { name: 'plan', title: 'Plan' },
    { name: 'measure', title: 'Measurements' },
] as const;

// The stages of each kind of entry, as `tools/wf/lib.ts` defines them.
export const STAGES: Record<string, string[]> = {
    milestone: ['plan', 'build', 'measure', 'publish'],
    decision: ['writeup', 'publish'],
    chore: ['plan', 'build', 'publish'],
};

export const STAGE_LABELS: Record<string, string> = {
    plan: 'Plan',
    build: 'Build',
    measure: 'Measure',
    publish: 'Publish',
    writeup: 'Writeup',
};

// The command that works on each stage.
export const STAGE_COMMANDS: Record<string, string> = {
    plan: '/wf-plan',
    build: '/wf-build',
    measure: '/wf-measure',
    publish: '/wf-publish',
    writeup: '/wf-writeup',
};

export const KIND_LABELS: Record<string, string> = {
    milestone: 'Milestone',
    decision: 'Decision',
    chore: 'Chore',
};

export const STATUS_LABELS: Record<string, string> = {
    active: 'In progress',
    done: 'Done',
    abandoned: 'Abandoned',
};
