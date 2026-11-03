---
summary: The Pi runs Raspberry Pi OS Trixie with ROS 2 Jazzy from RoboStack, installed with Pixi; the stamp epoch and the repository layout are still open.
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
and `pixi.lock` records every package by hash. The same manifest serves the development machine, so
bags can be replayed there with the same ROS packages.

### What was checked

These results come from solving the environment and unpacking its packages on an x86-64 machine, on
2026-10-30. Nothing has yet run on a Pi, and the [ledger](../../reference/open-questions/) tracks what
would close that (#29 and #30). This manifest solves for both platforms:

```toml
[workspace]
name = "fusion-box"
channels = ["https://prefix.dev/robostack-jazzy", "conda-forge"]
platforms = [{ platform = "linux-aarch64", glibc = "2.41" }, { platform = "linux-64", glibc = "2.41" }]

[dependencies]
ros-jazzy-ros-base = "*"
ros-jazzy-rosbag2-storage-mcap = "*"
ros-jazzy-rosidl-default-generators = "*"
compilers = "*"
cmake = "*"
ninja = "*"
colcon-common-extensions = "*"

[target.linux-aarch64.dependencies]
ros-jazzy-camera-ros = "*"
libcamera = { version = "*", build = "*rpi_fork" }
```

On arm64 it resolves to `camera_ros` 0.7.0, the `rpi_fork` build of libcamera 0.5.2 and Python 3.14,
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
- **Docker stays for Kalibr.** Kalibr ships only ROS 1 Dockerfiles, so `docker/kalibr` remains, though
  nothing on the box's recording path runs in a container.

### Alternatives

**Ubuntu 24.04 with native ROS 2** has the best ROS support and direct device access, but it carries
both kernel unknowns, and the checks in the
[ledger](../../reference/open-questions/#os-decision-evidence) would have to pass on a real image first.

**Raspberry Pi OS with ROS 2 in Docker** keeps Tier 1 packages, and it remains the fallback if the
RoboStack packages fail on the Pi. It lost because its costs are certain, in device passthrough, source
builds of libcamera and `camera_ros`, and another layer to debug, while the risks it avoids can be
tested directly: the packages as soon as the Pi is imaged, and libcamera when the camera arrives.

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

The repository holds the box's firmware, its ROS 2 workspace, the host-side services that must run
without ROS, the analysis tools, and the companion site:

```text
firmware/pico-trigger/   # Pico C SDK with PIO: the camera trigger
ros2_ws/src/
  sensor_box_msgs/       # messages with the arrival-time field
  ubx_driver/            # the F9R's UBX stream as ROS messages
  trigger_bridge/        # matches trigger times to camera frames
  sensor_box_bringup/    # launch files and parameters
host/ubx_mux/            # owns the F9R USB port; feeds chrony and the driver
tools/
  allan/                 # Allan variance of the IMU
  timing/                # timing analysis from the AD3 and the logs
  bag_tools/             # bag conversion and inspection
calib/                   # calibration targets, configs and results
system/                  # host configuration: chrony, systemd units, boot-config fragments
cad/                     # the enclosure
docker/
  kalibr/                # ROS 1 on Ubuntu 20.04, for Kalibr alone
site/                    # the companion site
pixi.toml                # the ROS 2 environment
pixi.lock                # committed
```

Four of these are not preferences. The stamping rule requires `sensor_box_msgs`, because an arrival
time cannot be recorded in a stock message. `host/ubx_mux` follows from time sync having to work
without ROS: only one process can own the F9R's USB port, and chrony needs coarse time from it.
`docker/kalibr` follows from Kalibr shipping only ROS 1 Dockerfiles. The Pixi files sit at the root
because the manifest is what a build enters from anywhere in the workspace, and `.pixi/` is ignored.

Milestone write-ups live in the archive, as each entry's `measure.md`, and the ledger and the
milestones are pages under `site/content/reference/`. Linting and formatting (`ruff`, `clang-format`,
`pre-commit`) are a chore for after this entry.

**Recommendation:** adopt this layout.

> [!TODO] Is this the repository layout?
> Adopt it as written, or say what should change?

## Consequences

Once these are settled, M0 can create the directories, M1's draft plan on the
[milestones page](../../reference/milestones/) can become a real plan, and `AGENTS.md` can state the
epoch rather than leaving it open.

What each position costs, and what lost and why, is written in its own section.
