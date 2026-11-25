import type { WorkflowConfig } from '@mvarble/mesearch-workflow';

// The box's development workflow: the kinds of entry, their stages, and what counts as the box's
// code. The engine (`bin/wf`) and the skills read it, and `mesearch-wf sync` writes
// `.agents/reference/mesearch/workflow.md` from it. It loads before anything is installed, so it
// imports nothing from a package but types.
export default {
    project: 'the box',
    // What counts as the box's code: changed only once an entry reaches `build`. The workflow's
    // own checks, under `tools/workflow/`, are not part of the box.
    code: [
        /^firmware\//,
        /^ros2_ws\//,
        /^host\//,
        /^system\//,
        /^calib\//,
        /^cad\//,
        /^docker\//,
        /^tools\/(?!workflow\/)[^/]+\//,
    ],
    // The ledger of unverified facts records what is known as soon as it is known, at any stage.
    free: ['site/content/reference/open-questions/'],
    describe: {
        code: '`firmware/`, `ros2_ws/`, `host/`, `system/`, `calib/`, `cad/`, `docker/`, and `tools/` other than `tools/workflow/`',
        free: 'the ledger, `site/content/reference/open-questions/`,',
    },
    kinds: {
        milestone: {
            stages: ['plan', 'build', 'measure', 'publish'],
            describe: "one row of the milestones table, ending in measured numbers",
        },
        probe: {
            stages: ['measure', 'publish'],
            describe:
                'one session at the bench, written up as a lab that usually closes ledger rows; it writes no box code',
        },
        decision: {
            stages: ['writeup', 'publish'],
            describe: 'a position the project takes, argued in prose',
        },
        chore: {
            stages: ['plan', 'build', 'publish'],
            describe: 'a refactor or tooling change with nothing to measure',
        },
    },
    stages: {
        plan: {
            document: true,
            unlocks: ['math'],
            checklist: true,
            editableDuring: ['build'],
            describe: '`plan.md`: a checklist, and what the milestone must measure',
        },
        build: {
            unlocks: ['code'],
            describe: "the code and config, committed as the plan's boxes are ticked",
        },
        measure: {
            document: true,
            sections: ['Results'],
            describe: '`measure.md`: the method and the measured results',
        },
        publish: {
            unlocks: ['pages'],
            describe: "the pages that say what now _is_, and the entry's `index.md`",
        },
        writeup: {
            document: true,
            unlocks: ['math'],
            describe: "`writeup.md`: a decision's argument",
        },
    },
    pagesOptional: ['chore'],
} satisfies WorkflowConfig;
