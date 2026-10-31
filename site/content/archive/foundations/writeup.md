---
summary: Which OS the Pi runs, which epoch stamps count from, and how the repository is laid out; each with a recommendation, and none yet decided.
---

## Context

M1 cannot start until three things are settled. It installs an OS and a kernel overlay on the Pi, its
measurements compare stamps with the system clock, and its code needs somewhere to live. Each of
these is cheap to choose now and expensive to change after M4, when the camera, the recorder and the
calibration tooling all depend on it.

The facts below come from vendor documents. None has been measured on this hardware yet, and the
[ledger](../../reference/open-questions/) tracks what would close each one.

## Operating system

The kickoff assumed Ubuntu 24.04 with native ROS 2 Jazzy, and left open a fallback to Raspberry Pi OS
with ROS 2 in Docker if the camera's trigger tooling needed it. The camera's trigger is the riskiest
part of the build, so it should decide this.

| Concern | Ubuntu 24.04, native ROS 2 | Raspberry Pi OS, ROS 2 in Docker |
| --- | --- | --- |
| ROS 2 support | Tier 1 on arm64 | Tier 1 in the container, Tier 3 on the host |
| Innomaker trigger and strobe | Ubuntu is not mentioned | Documented on the Pi 5 for Bookworm and Trixie |
| `imx296.trigger_mode` | Unverified on Ubuntu's kernel | Present in the Pi kernel's `rpi-6.12.y` |
| `pps-rp1` overlay with echo | Needs Pi kernel `1:6.12.70-1+rpt1` or later; the noble listing suggests a 6.8 base, unconfirmed | Available from that kernel on |
| libcamera for the Pi 5 | Build the `raspberrypi` fork from source | The same build, inside the image |
| Device access | Direct | Pass through media, video, subdev, DMA heap and serial devices |

The libcamera build is the same work either way, so it does not separate them. What separates them is
that Ubuntu's two unknowns, the camera trigger and the PPS overlay, both sit in the kernel, which is
the one thing a container cannot change. Docker's cost is real but known: device passthrough, and one
more layer to debug. Time sync is unaffected, because chrony and the process that owns the F9R's port
run on the host under either choice.

**Recommendation:** Raspberry Pi OS Trixie, with ROS 2 Jazzy in Docker.

> [!TODO] Which OS does the Pi run?
> Raspberry Pi OS Trixie with ROS 2 in Docker, as recommended, or Ubuntu 24.04 with native ROS 2? If
> Ubuntu, the checks in the [ledger](../../reference/open-questions/#os-decision-evidence) come first,
> on a real image.

## The epoch of header.stamp

The stamping rule says "the GPS timebase", which fixes the clock but not the number. GPS time and
UTC tick together and differ by a whole number of leap seconds, currently 18, so a stamp has to choose
one to count from. The rule cannot be implemented until it does.

| | UNIX nanoseconds (GPS time minus leapS) | Continuous GPS time |
| --- | --- | --- |
| Compared with the system clock | Directly | Off by leapS, so every latency diagnostic needs a correction |
| ROS tools, bag log times | Line up | Stamps sit 18 s from everything else |
| Across a leap second | Steps, in a bag recorded through one | Continuous |
| Against PPK ground truth | Converted once | Native |

A leap second would be the one case where UNIX stamps misbehave, and it can be handled: keep raw week
and time of week in `sensor_box_msgs`, so that continuous GPS time can always be recovered. In the
other direction, nothing can stop a tool that assumes UNIX time from quietly misreading a GPS stamp.

Whichever is chosen, the conversion happens in one helper only, and leapS comes from `UBX-NAV-TIMELS`
and is never hardcoded. Separately, `CFG-TP-TIMEGRID_TP1` is set to GPS either way: it defaults to UTC, and on UTC a cold start can wait up to 12.5 minutes for the UTC parameters before the first pulse.

**Recommendation:** UNIX nanoseconds, computed as GPS time minus leapS.

> [!TODO] Which epoch does header.stamp count from?
> UNIX nanoseconds, as recommended, or continuous GPS time?

## Repository layout

The kickoff's suggested layout holds, with these changes:

```text
firmware/pico-trigger/   # Pico C SDK with PIO
ros2_ws/src/
  sensor_box_msgs/       # new: adds the arrival-time field
  ubx_driver/
  trigger_bridge/
  sensor_box_bringup/
host/ubx_mux/            # new: owns the F9R USB port
tools/
  allan/
  timing/
  bag_tools/
calib/
system/
cad/
docker/
  kalibr/                # new: ROS 1, Ubuntu 20.04
  ros2/                  # new: only if the OS is Pi OS
site/                    # replaces docs/
```

Three of these are not preferences. The stamping rule requires `sensor_box_msgs`, because an arrival
time cannot be recorded in a stock message. `host/ubx_mux` follows from time sync having to work
without ROS: only one process can own the F9R's USB port, and chrony needs coarse time from it. And
`docker/kalibr` follows from Kalibr shipping only ROS 1 Dockerfiles.

The workflow changes one thing about the kickoff: milestone write-ups live in the archive, as each
entry's `measure.md`, rather than in `docs/`. The ledger and the milestones are pages under
`site/content/reference/`. M0's linting and formatting setup (`ruff`, `clang-format`, `pre-commit`)
is a chore for after this entry.

**Recommendation:** adopt this layout.

> [!TODO] Is this the repository layout?
> Adopt it as written, or say what should change?

## Consequences

Once these are settled, M0 can create the directories, M1's draft plan on the
[milestones page](../../reference/milestones/) can become a real plan, and `AGENTS.md` can state the
epoch rather than leaving it open.

What each answer costs, and what lost and why, are written here as the questions above are answered.
