---
title: "The foundations: OS, stamp epoch, repository layout"
pages:
    - start/what-the-box-is
    - reference/milestones
    - reference/open-questions
---

The positions the box builds on. The Pi runs Raspberry Pi OS Trixie, with ROS 2 Jazzy from RoboStack
installed through Pixi, so that the kernel the camera trigger and the PPS overlay need is the one the
vendor documents, and no container sits between the nodes and the hardware. `header.stamp` counts
UNIX nanoseconds, from the receiver's GPS time and the leap-second count it reports once that count is
valid. Calibration runs offline in Kalibr, in a ROS 1 container, and the repository is laid out flat.
