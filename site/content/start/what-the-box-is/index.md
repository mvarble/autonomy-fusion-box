---
title: What the box is
summary: The goal, the hardware on the bench, and the architecture as it has been decided so far.
order: 1
---

The box is a portable, battery-powered recorder for GNSS, IMU and camera data on one GPS-disciplined
timebase. Later it will also run fusion onboard. It is a personal project for hands-on sensor-fusion
experience, which is why each milestone has to end in real numbers. Nothing has been built yet, so
this page describes the intent. Anything it says about the hardware is a claim until the
[open questions](../../reference/open-questions/) say otherwise.

## The hardware

| Item                                                                       | Role                                                         |
| -------------------------------------------------------------------------- | ------------------------------------------------------------ |
| ArduSimple simpleRTK2B Fusion (u-blox ZED-F9R)                             | RTK GNSS and internal IMU; the master clock                  |
| Existing SD logger board                                                   | Independent raw-UBX backup, for PPK ground truth with RTKLIB |
| Raspberry Pi 5 4 GB with Active Cooler                                     | Main computer                                                |
| Innomaker CAM-MIPI296RAW (Sony IMX296 mono global shutter, 1456×1088, M12) | Camera                                                       |
| Raspberry Pi Pico                                                          | Trigger generator, locked to the PPS                         |
| Digilent Analog Discovery 3                                                | Scope and logic analyzer for scripted timing measurements    |
| USB-C panel-mount extension and PD power banks                             | One power input; expect 5 V at 3 A only                      |

## The architecture

**Time.** GPS time is the master clock. The F9R's TIMEPULSE at 1 PPS goes to a Pi GPIO, where chrony
disciplines the system clock, and to the Pico, which generates camera triggers at known GPS times.

**The stamping rule.** `header.stamp` is the measurement time on the GPS timebase, set at the source.
Arrival time at the Pi is recorded separately, for latency diagnostics only.

**Software.** ROS 2 Jazzy, a thin UBX node of our own so that we control the stamps, `camera_ros` for
frames, and MCAP bags split every few minutes. Calibration runs offline in Kalibr. Onboard fusion
comes later: a GTSAM GNSS and IMU factor graph, then mono VIO.

**Power.** One USB-C PD input to the Pi, which powers the F9R and the Pico over USB and the camera
over CSI.

**Mechanical.** One rigid plate carries the F9R board and the camera, with nothing compliant between
the IMU and the camera. The Pi and power hardware sit in a shell around it.
