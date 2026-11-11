# fusion box

A portable, battery-powered box that collects GNSS, IMU and camera data, puts it all on one
GPS-disciplined timebase, and records it. Later it also runs fusion onboard. It is a personal
project for hands-on sensor-fusion experience, so every milestone ends in a short write-up with
real numbers: timing jitter, Allan variance parameters, calibration residuals, ATE and RPE against
ground truth.

## Working with the user

- They are a navigation and state-estimation engineer (GTSAM factor graphs, IMU and RF ranging
  fusion, ROS 2) who writes C++ and Python daily. Skip basic explanations.
- Be direct. Point out pitfalls rather than reassuring. Prefer short, checkable task lists.
- Ask before decisions that are expensive to reverse: OS choice, repo-wide structure, anything that
  writes to the Pi's boot config, and any write to the F9R's flash.

## The stamping rule (non-negotiable)

- `header.stamp` is the measurement time on the GPS timebase, set at the source. It is never the
  arrival time at the Pi.
- Arrival time goes in a separate field, for latency diagnostics only.
- A camera frame's time is its mid-exposure, not its trigger edge, and frames are matched to
  triggers by time, never by counting frames alone.
- Data is not trusted while `UBX-TIM-TP` reports `TpNotLocked`.
- `header.stamp` counts UNIX nanoseconds: the receiver's GPS time minus the leap-second count it
  reports, converted in one helper and nowhere else. The count is never hardcoded, and is used only
  once `UBX-NAV-TIMEGPS` sets `leapSValid` and `UBX-NAV-TIMELS` gives a source other than the
  firmware's default; until then nothing is recorded. Messages keep the raw GPS week and time of week.

## Unverified facts

`site/content/reference/open-questions/index.md` is the one list. Do not build on an item until its
status allows it: MEASURED, or DOC where a vendor's specification is enough. Cite the document and
section, or the measurement. Never present a third party's number as this box's, and never write a
number from memory.

## F9R configuration

Set keys by name with `VALSET` and confirm each with `VALGET`, in RAM and BBR only. Check
`UBX-MON-VER` first, because the key list depends on the firmware.

## How to work here

**Conversation is the default.** Answer questions, explain things and sketch ideas in the reply:
none of that needs a workflow, and none of it should start one.

**The development workflow runs only when the user invokes it**, through the `/wf-*` commands
(`.agents/skills/wf-*`). Every change to the box's code goes through an entry. The procedure is in
`.agents/reference/workflow.md`. In short:

| command                                                  | what it does                                 |
| -------------------------------------------------------- | -------------------------------------------- |
| `/wf-start <slug> <milestone\|probe\|decision\|chore>`   | open an entry on this branch                 |
| `/wf-writeup`                                            | draft and revise a decision's argument       |
| `/wf-plan`                                               | draft and revise the plan                    |
| `/wf-build`                                              | work through the approved plan, task by task |
| `/wf-measure`                                            | write up the method and the measured results |
| `/wf-publish`                                            | bring the pages up to date                   |
| `/wf-approve`, `/wf-reopen`, `/wf-abandon`, `/wf-resume` | move the entry; the user's alone to give     |
| `/wf-status`                                             | where things stand                           |

Rules that hold whether or not a command was invoked:

- Never start, approve, reopen, abandon or resume an entry on your own judgment, and never run
  `bin/wf start|approve|reopen|abandon|resume` except inside the skill the user invoked for it.
- Never do a stage's work outside its skill. Asked to write code with no entry at the build stage,
  say so and point to the command that would get there.
- `bin/wf guard` runs before every edit in Claude Code (`.claude/settings.json`) and refuses one
  the stage does not allow. Do not work around a refusal; it is telling you which command the
  user would need to give.
- When work at one stage shows an earlier stage wrong, stop and say so; the user may reopen it.
- Not gated: the workflow's tool (`bin/wf`, `tools/wf/`), the skills, CI, the site's own code
  (`site/src/`), and the ledger. Changes to those are ordinary work.

## Layout

| path                  | what it is                                                   |
| --------------------- | ------------------------------------------------------------ |
| `site/`               | the companion site; `site/README.md` says how it works       |
| `site/content/`       | pages, math notes, the ledger, and the archive of entries    |
| `bin/wf`, `tools/wf/` | the workflow's command line and its tests                    |
| `.workflow/active`    | the entry this branch works on, written by `bin/wf` alone    |
| `.agents/skills/`     | the skills (linked into `.claude/skills/` for Claude Code)   |
| `.agents/reference/`  | `workflow.md` (the procedure), `authoring.md` (how to write) |

The box's own directories, decided in the `foundations` entry and created in M0, sit flat at the top
level: `firmware/` (the Pico), `ros2_ws/` (the ROS 2 workspace), `host/` (services that must run
without ROS, such as `ubx_mux`), `system/` (host configuration), `tools/` (analysis), `calib/`,
`cad/`, and `docker/` (Kalibr's ROS 1 container). ROS 2 comes from the Pixi manifest at the root, not
from apt or a container.

## Commits

Commit each revision of a document and each task of a plan, once the user has asked for the
workflow to run. The first line says what changed, as an imperative sentence; the body, when there
is one, says why.

## Checks

```sh
bin/wf check
node --test 'tools/*/*.test.ts' && site/node_modules/.bin/tsc -p tools
cd site && pnpm check && pnpm lint && pnpm test && pnpm build
```

CI (`.github/workflows/ci.yml`) runs the same, and `bin/wf check --merge` on pull requests into
`main`. A push to any branch that passes publishes the site to
<https://mvarble.github.io/autonomy-fusion-box/>, drafts included, so the site shows the latest
push.
