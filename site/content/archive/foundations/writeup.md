---
summary: The Pi runs Raspberry Pi OS Trixie with ROS 2 Jazzy from RoboStack, installed with Pixi; `header.stamp` counts UNIX nanoseconds, GPS time minus leap seconds; calibration runs in Kalibr, in a ROS 1 container; and the repository is laid out flat, by kind.
---

## Context

M1 cannot start until three things are settled. It installs an OS and a kernel overlay on the Pi, its
measurements compare stamps with the system clock, and its code needs somewhere to live. Each of
these is cheap to choose now and expensive to change after M4, when the camera, the recorder and the
calibration tooling all depend on it.

The facts below come from vendor documents. None has been measured on this hardware yet, and the
[ledger](../../reference/open-questions/) tracks what would close each one.

## Operating system

**Decision:** the Pi runs 64-bit Raspberry Pi OS Trixie. ROS 2 Jazzy comes from
[RoboStack](https://robostack.github.io/GettingStarted.html), the conda packaging of ROS, installed
with [Pixi](https://pixi.sh) and pinned by a committed `pixi.lock`. ROS 2 is not installed with apt or
run in a container. Chrony and the kernel overlays stay on the host, and time sync must keep working
without ROS, so the process that owns the F9R's port does not depend on it. Which toolchain builds that
process is left to M1.

This is two choices, and they differ in what it costs to be wrong. The OS is expensive to change.
The way ROS 2 reaches it is not: moving from Pixi to a container changes how the workspace is
packaged, and leaves its source alone.

The camera's trigger is the riskiest part of the build, so it decides the OS. Ubuntu 24.04 is the
usual home of ROS 2 Jazzy, but its two unknowns on the Pi 5, the camera trigger and the PPS overlay,
both sit in the kernel. Neither Pixi nor a container can change the kernel, whereas Raspberry Pi OS
carries both, and the camera vendor documents its trigger on it.

| Concern | Ubuntu 24.04, native | Pi OS, Docker | Pi OS, Pixi |
| --- | --- | --- | --- |
| ROS 2 packages | Tier 1 on arm64 | Tier 1, inside the Ubuntu container | RoboStack: community-built, with no tier in ROS's own support table |
| Innomaker trigger and strobe | Ubuntu is not mentioned | Documented on the Pi 5 for Bookworm and Trixie | The same |
| `imx296.trigger_mode` | Unverified on Ubuntu's kernel | Present in the Pi kernel's `rpi-6.12.y` | The same |
| `pps-rp1` overlay with echo | Needs Pi kernel `1:6.12.70-1+rpt1` or later; the noble listing suggests a 6.8 base, unconfirmed | Available from that kernel on | The same |
| libcamera for the Pi 5 | Build the `raspberrypi` fork from source | The same build, inside the image | Prebuilt `rpi_fork` from conda-forge, unproven against Trixie's kernel |
| `camera_ros` | Build from source | Build from source | Prebuilt |
| Device access | Direct | Pass through media, video, subdev, DMA heap and serial devices | Direct |

Once the OS is Raspberry Pi OS, a container's only job is to supply the ROS userspace, and Pixi supplies
that with no namespace boundary: no device passthrough, no container networking for DDS, and one less
layer between a stamp and the hardware. It also removes the libcamera and `camera_ros` source builds,
and `pixi.lock` records every package by hash. The same manifest serves the development machine, and
the two environments are solved together, so a bag is replayed there with the same ROS packages it
was recorded with.

### What was checked

These results come from solving the environment and unpacking its packages on an x86-64 machine, on
2026-10-30, and the manifest below was solved again on 2026-11-03. Nothing has yet run on a Pi, and the
[ledger](../../reference/open-questions/) tracks what would close that (#29 and #30). The manifest has
one environment for the box, on the Pi alone, and one for development, on either machine; the
repository's layout below explains the split:

```toml
[workspace]
name = "fusion-box"
channels = ["https://prefix.dev/robostack-jazzy", "conda-forge"]
platforms = [
    { name = "pi", platform = "linux-aarch64", glibc = "2.41" },
    { name = "x86", platform = "linux-64", glibc = "2.41" },
]

[dependencies]
ros-jazzy-ros-base = "*"
ros-jazzy-rosbag2-storage-mcap = "*"
ros-jazzy-rosidl-default-generators = "*"
compilers = "*"
cmake = "*"
ninja = "*"
colcon-common-extensions = "*"

[feature.box]
platforms = ["pi"]

[feature.box.dependencies]
ros-jazzy-camera-ros = "*"
libcamera = { version = "*", build = "*rpi_fork" }

[feature.dev.dependencies]
rosbags = "*"
numpy = "*"
scipy = "*"
matplotlib = "*"

[environments]
box = { features = ["box"], solve-group = "ros" }
dev = { features = ["dev"], solve-group = "ros" }
```

In the `box` environment it resolves to `camera_ros` 0.7.0, the `rpi_fork` build of libcamera 0.5.2 and Python 3.14,
from RoboStack's newest series (`ros2-distro-mutex` 0.20). That libcamera build contains the PiSP IPA
module, tuning files for `imx296` and `imx296_mono`, and libcamera's `cam` tool. Two parts of the
manifest change what gets installed, and leaving either out produces no error:

- **`glibc = "2.41"`.** libcamera 0.5.2 requires glibc 2.34 or later, and Pixi assumes an older glibc
  unless told otherwise. Without this declaration the solve still succeeds, but it walks back to
  `camera_ros` 0.6.0 and libcamera 0.5.1 from the much older series 0.14. Debian Trixie ships glibc
  `2.41-12+deb13u4`.
- **`build = "*rpi_fork"`.** The upstream build of libcamera also contains the PiSP pipeline, but at
  0.5.2 its build number (106) is higher than the fork's (6), so a bare dependency installs upstream.
  The fork is what `camera_ros` directs a Pi 5 to, and it is the line Raspberry Pi OS follows, so it is
  the build closest to what the camera's vendor documents.

The lockfile, not the manifest, holds the series, so the box stays on one until it is deliberately
relocked. libcamera stays at 0.5.x in every series because `ros2-libcamera` requires it below 0.6, so
moving to libcamera 0.7.1 would mean building `camera_ros` from source. Series 0.19 with Python 3.12
also solves, and is the first thing to try if Python 3.14 causes trouble: the newest series is built
for it, though RoboStack's `conda_build_config.yaml` on `main` still listed Python 3.12.

The Pi 5's default kernel, `kernel_2712.img`, uses 16K pages, which has broken binaries built for
smaller pages. This exposure is not specific to Pixi, because a container shares the host's kernel. The
evidence so far is indirect. Pixi's own arm64 binary failed in exactly this way in 2025, the fix set
jemalloc's page size in its release builds, and a build script on `main` still sets it. All 221 ELF
files in a sample of 17 of the environment's 495 arm64 packages, including libcamera, `rclcpp`,
`rmw_fastrtps_cpp`, CycloneDDS, the MCAP storage plugin and OpenCV, have 64K segment alignment, so they
should load. That does not rule out code that assumes a 4K page at run time. If something does, the
remedy is `kernel=kernel8.img`, which is a boot-config write and needs its own approval.

### What it costs

- **Support.** RoboStack is a community project, and ROS's support tiers do not cover it. A bug that
  reproduces only here is ours to chase, with Docker as the way to find out whether the packaging is
  to blame.
- **A frozen environment.** A locked environment receives no fixes until it is relocked, and relocking
  can move every package at once. That is a deliberate change: it gets committed, and the timing
  measurements get repeated.
- **Two libcameras.** `rpicam-apps` is not on conda-forge, so the vendor's bring-up steps use the
  host's apt libcamera while ROS uses the environment's. A trigger test passing under one says nothing
  about the other, so the camera's measurements run through `cam` or `camera_ros` from the environment.
- **Activation.** Nothing in the workspace works outside the environment, so every systemd unit that
  runs ROS has to enter it through Pixi. Apt's ROS packages must never be sourced alongside it.

### Alternatives

**Ubuntu 24.04 with native ROS 2** has the best ROS support and direct device access, but it carries
both kernel unknowns, and the checks in the
[ledger](../../reference/open-questions/#os-decision-evidence) would have to pass on a real image first.

**Raspberry Pi OS with ROS 2 in Docker** keeps Tier 1 packages, and it remains the fallback if the
RoboStack packages fail on the Pi. It lost because its costs are certain, in device passthrough, source
builds of libcamera and `camera_ros`, and another layer to debug, while the risks it avoids can be
tested directly: the packages as soon as the Pi is imaged, and libcamera when the camera arrives.

## The epoch of header.stamp

**Decision:** `header.stamp` counts UNIX nanoseconds, computed from the receiver's GPS time by
subtracting the leap-second count the receiver reports. The clock is still the GPS timebase, as the
stamping rule requires; this fixes only the number it is written in.

GPS time and UTC tick together and differ by a whole number of leap seconds: GPS is 18 s ahead of UTC
since the leap second at the end of 2016 ([USNO](https://www.cnmoc.usff.navy.mil/Our-Commands/United-States-Naval-Observatory/Precise-Time-Department/Global-Positioning-System/USNO-GPS-Time-Transfer/Leap-Seconds/)),
and IERS Bulletin C 72 announced no leap second for the end of December 2026 ([IERS](https://datacenter.iers.org/data/latestVersion/bulletinC.txt)). UNIX time ignores leap
seconds, so one helper converts a GPS week, time of week and leap-second count into a stamp:

$$
	t_{\mathrm{ns}} = 10^9 \left( 315\,964\,800 + 604\,800\, w - \ell \right) + t_{\mathrm{tow,ns}}
$$

Here $w$ is the full GPS week, $t_{\mathrm{tow,ns}}$ the time of week in nanoseconds (`iTOW` in
milliseconds plus `fTOW` in nanoseconds, from `UBX-NAV-TIMEGPS`), $\ell$ the leap-second count, and
315 964 800 s the GPS epoch, 1980-01-06, in UNIX seconds. Every timestamped source, from the receiver's
navigation solution to the trigger edges and, once its mapping is known (#10), the IMU's time tags,
goes through this helper and no other.

The stamp's value is UNIX time, but its source is never the Pi's system clock. The helper uses the
receiver's GPS time, and the system clock is used only for the arrival time.

### Where the leap-second count comes from

The count is read from the receiver, never written in the code. `UBX-NAV-TIMEGPS` carries it as
`leapS` with a `leapSValid` flag, and `UBX-NAV-TIMELS` says where it came from: `srcOfCurrLs = 0`
means "Default (hardcoded in the firmware, can be outdated)" ([ID §3.15.25–26](../../reference/open-questions/#sources)).
So a stamp exists only once `leapSValid` is set and the source is a constellation, not the firmware's
default. Until then the box records nothing, just as it trusts nothing while `UBX-TIM-TP` reports
`TpNotLocked`. How long that takes after a cold start, and whether the count survives a power cycle
in battery-backed RAM, are unmeasured (#9, #31).

`CFG-TP-TIMEGRID_TP1` is set to GPS. It defaults to UTC, and on UTC a cold start can wait up to 12.5
minutes for the UTC parameters before the first pulse. On the GPS grid the pulse marks the same instant
either way, because the two scales differ by whole seconds.

### What it costs

- **A leap second steps the stamps.** Through a positive leap second, UNIX time repeats a second, so
  a bag recorded across one has a second of ambiguous stamps. `sensor_box_msgs` therefore keeps each
  measurement's raw GPS week and time of week beside `header.stamp`, and continuous GPS time can always
  be recovered. `UBX-NAV-TIMELS` announces a coming leap second, so a recording that would cross one
  can be flagged in advance.
- **Ground truth needs one conversion.** PPK solutions are in GPS time, so they pass through the same
  helper before being compared with the box's estimates.
- **A wait at a cold start.** Nothing records until the leap-second count is valid.

What this buys is that stamps compare directly with the system clock, so latency diagnostics need no
correction, and ROS tools, bag times and plotting all agree with the stamps.

### Alternatives

**Continuous GPS time**, counted from the GPS epoch or from 1970 without leap seconds, never steps
and matches PPK natively. It lost because it puts every stamp 18 s from the system clock and from
every tool that assumes UNIX time. Nothing marks such a stamp as different, so a tool that assumes
UNIX time misreads it silently, whereas the leap-second step of UNIX stamps is rare, announced, and
recoverable from the raw fields.

## Calibration

**Decision:** camera intrinsics, and the camera-to-IMU transform and time offset, are calibrated
offline on the development machine with [Kalibr](https://github.com/ethz-asl/kalibr), run in a
container built from its `Dockerfile_ros1_20_04`. This belongs with the foundations because it is
the one place the repository needs a container.

Kalibr reads only ROS 1 bags, and its repository ships only ROS 1 Dockerfiles, for Ubuntu 16.04,
18.04 and 20.04. Calibration runs once per change to the camera or its mounting, offline, so a ROS 1
container for it costs little: nothing on the box's recording path runs in a container, and nothing
outside `docker/kalibr` touches ROS 1. In return the box uses the camera-IMU calibrator that most
work is compared against.

Recordings reach Kalibr as ROS 1 bags written by `rosbags`, a Python library that needs no ROS (#25).
Kalibr's bag readers (`ImageDatasetReader.py` and `ImuDatasetReader.py`, read on `master` on
2026-11-03) take every time from `header.stamp`, so the stamping rule reaches the calibration
unchanged: the exporter copies stamps and does not make them. Two of Kalibr's options would break
that, and are never used:

- **`--perform-synchronization`** corrects each `header.stamp` against the bag's record time, which
  is arrival time. That is exactly what the stamping rule forbids.
- **`--no-time-calibration`** fixes the time offset at zero, so it would hide the very offset that
  checks the timing chain.

`--timeoffset-padding` bounds how far the time offset may move during estimation, 30 ms by default.
If the box's timing is right the offset is far smaller, so a result pressed against that bound means
the timing is wrong, not that the bound is too tight.

### What it costs

- **A container, and an aging toolchain.** The image is Ubuntu 20.04 with ROS 1, and Kalibr's last
  commit was on 2024-03-08. The image is built once and kept, so a calibration can be rerun on the
  same tool later (#24).
- **An export step.** Every calibration recording goes through MCAP-to-ROS 1 conversion, which has to
  keep stamps exact (#25).
- **The time offset is still not a check.** Kalibr's time offset only checks the timing chain if
  frames are stamped at mid-exposure and the IMU's delay is already measured (#26). Otherwise it is
  the only measurement of that delay.

### Alternatives

**[Basalt](https://gitlab.com/VladyslavUsenko/basalt)** estimates the same quantities with no ROS
installed and ships a Linux binary. It lost on standing rather than function: Kalibr is the reference
a result is compared against, and for a calibration run once, the container costs less than the
doubt. Basalt's bag reader also takes every time from `header.stamp`, so it remains a cross-check that
reads the same export. Its reader for EuRoC folders is fixed at two cameras, so it would need the bag
too.

**Kalibr built from source in a ROS 1 Pixi environment** avoids the container but not ROS 1. Neither
RoboStack's `robostack-noetic` and `robostack-staging` channels nor conda-forge packaged Kalibr on
2026-11-03, so it would be a source build of a catkin workspace, for one tool.

## Repository layout

**Decision:** the repository is laid out flat, by kind: the box's firmware, its ROS 2 workspace, the
host-side services that must run without ROS, the analysis tools, calibration, system configuration
and the enclosure each have a directory at the top level, beside the companion site.

```text
firmware/pico-trigger/   # Pico C SDK with PIO: the camera trigger
ros2_ws/src/
  sensor_box_msgs/       # messages with the arrival-time field, and raw GPS week and time of week
  ubx_driver/            # the F9R's UBX stream as ROS messages
  trigger_bridge/        # matches trigger times to camera frames
  sensor_box_bringup/    # launch files, parameters, and the adopted calibration
host/ubx_mux/            # owns the F9R USB port; feeds chrony and the driver
tools/
  allan/                 # Allan variance of the IMU
  timing/                # timing analysis from the AD3 and the logs
  bag_tools/             # bag inspection, and the MCAP-to-ROS 1 export for Kalibr
  wf/                    # the workflow's tool: not the box's
calib/                   # target configs, Kalibr runs and their results
system/                  # host configuration: chrony, systemd units, boot-config fragments
cad/                     # the enclosure and the sensor plate
docker/
  kalibr/                # ROS 1 on Ubuntu 20.04, for Kalibr alone
site/                    # the companion site
bin/wf                   # the workflow's command line
pixi.toml                # the box and dev environments
pixi.lock                # committed
```

Four of these are not preferences. The stamping rule requires `sensor_box_msgs`, because an arrival
time cannot be recorded in a stock message. `host/ubx_mux` follows from time sync having to work
without ROS: only one process can own the F9R's USB port, and chrony needs coarse time from it.
`docker/kalibr` follows from Kalibr shipping only ROS 1 Dockerfiles. The Pixi files sit at the root
because the manifest is what a build enters from anywhere in the workspace, and `.pixi/` is ignored.

This is the layout `bin/wf` already assumes: its code areas (`firmware/`, `ros2_ws/`, `host/`,
`system/`, `calib/`, `cad/`, `docker/`, and `tools/` other than `tools/wf/`, in `tools/wf/lib.ts`)
are exactly these directories, so the workflow's tool needs no change when they are created.

Milestone write-ups live in the archive, as each entry's `measure.md`, and the ledger and the
milestones are pages under `site/content/reference/`. Linting and formatting (`ruff`, `clang-format`,
`pre-commit`) are a chore for after this entry.

### What it costs

- **Deployment is not visible in the paths.** What goes on the Pi (`ros2_ws/`, `host/`, `system/`)
  and what runs on a development machine (`tools/`, `calib/`, `docker/`) sit side by side, and the
  Pixi environments, not the directories, say which is which.
- **`tools/` holds one stranger.** The workflow's own tool, `tools/wf/`, is not the box's and is not
  gated, though it sits beside the analysis. The exception is one path, and the workflow already makes
  it.

### Alternatives

**Separating by where code runs**, with the deployed code in one directory and the development tools
and the physical design in others, would make deployment visible in every path. It lost because it
adds a level to every path and a convention to keep, for a distinction that the directory names and
the Pixi environments already make plain.

**Two repositories** would separate the box from its analysis mechanically, but they would split every
change that touches both sides, such as a new message field and the analysis that reads it, into two
commits in two histories.

## Consequences

With these settled, M0 can create the directories, M1's draft plan on the
[milestones page](../../reference/milestones/) can become a real plan, and `AGENTS.md` can state the
epoch.

What each position costs, and what lost and why, is written in its own section.
