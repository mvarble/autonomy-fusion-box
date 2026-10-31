import { defineGraph } from '$lib/graph/spec';

// The stages of an entry and the commands that move it between them. A chore joins a milestone's
// route at the plan but skips the measurements, and every kind ends in publishing.

export const workflow = defineGraph({
    title: 'The workflow',
    caption:
        '/wf-start opens an entry at the first stage of its kind, and /wf-approve moves it to the ' +
        'next. /wf-reopen takes it back to any earlier stage, of which only the step from the ' +
        'measurements to the plan is drawn. A decision goes from its writeup straight to publishing, ' +
        'and a chore from its build.',
    width: 900,
    height: 400,
    nodeRadius: 52,
    fontSize: 15,
    nodeKinds: {
        endpoint: { name: 'Opening and finishing an entry', hue: 'gray' },
        document: {
            name: 'A stage that writes a document, frozen once approved',
            hue: 'blue',
            shape: 'square',
        },
        code: { name: 'The stage that does the work', hue: 'green', shape: 'square' },
        pages: { name: 'The stage that writes the pages', hue: 'orange', shape: 'square' },
    },
    edgeKinds: {
        approve: { name: '/wf-approve' },
        reopen: { name: '/wf-reopen <stage>', hue: 'red', line: 'dashed' },
    },
    nodes: [
        { id: 'start', x: 50, y: 230, r: 34, kind: 'endpoint', label: 'Start' },
        { id: 'writeup', x: 200, y: 345, kind: 'document', label: 'Writeup' },
        { id: 'plan', x: 200, y: 150, kind: 'document', label: 'Plan' },
        { id: 'build', x: 370, y: 150, kind: 'code', label: 'Build' },
        { id: 'measure', x: 540, y: 150, kind: 'document', label: 'Measure' },
        { id: 'publish', x: 710, y: 230, kind: 'pages', label: 'Publish' },
        { id: 'done', x: 850, y: 230, r: 34, kind: 'endpoint', label: 'Done' },
    ],
    edges: [
        { from: 'start', to: 'writeup' },
        { from: 'start', to: 'plan' },
        { from: 'plan', to: 'build', kind: 'approve' },
        { from: 'build', to: 'measure', kind: 'approve' },
        { from: 'measure', to: 'publish', kind: 'approve' },
        { from: 'writeup', to: 'publish', kind: 'approve' },
        { from: 'build', to: 'publish', kind: 'approve', via: [[540, 50]], curve: 'bezier' },
        { from: 'publish', to: 'done', kind: 'approve' },
        { from: 'measure', to: 'plan', kind: 'reopen', bend: -30 },
    ],
});
