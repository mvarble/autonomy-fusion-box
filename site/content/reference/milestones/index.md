---
title: Milestones
summary: The nine milestones from repository scaffolding to fusion, and the draft plan for the first measurement.
order: 1
---

Each milestone is opened with `/wf-start <slug> milestone` and ends in measurements. None has been
started. The camera arrives November 16–29, which sets the earliest date for M4.

|     | Milestone                      | What it must show                                                                                                    |
| --- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| M0  | Repository scaffolding         | The layout, once the `foundations` entry settles it                                                                  |
| M1  | Time base                      | chrony locked to PPS; PPS-to-system-clock bias and jitter, measured with the AD3                                     |
| M2  | UBX logging and Allan variance | `ESF-RAW` and `NAV-PVT` published; noise density and bias random walk from a multi-hour static log, with temperature |
| M3  | Pico trigger firmware          | PPS-locked triggers with a sequence counter; histogram of edge offsets over hours                                    |
| M4  | Camera bring-up                | Trigger mode working; trigger-to-exposure latency; PPS-driven LED test; dropped-frame detection                      |
| M5  | Recorder service               | Bag splitting, button and LED, systemd, read-only root, data partition                                               |
| M6  | Calibration                    | Camera intrinsics, and camera–IMU extrinsics and time offset in Kalibr                                               |
| M7  | Power and case                 | Power measurements, sensor plate CAD, flex test, the shell                                                           |
| M8  | Fusion                         | GTSAM GNSS/IMU with a simulated outage test, then OpenVINS, against PPK ground truth                                 |

## M1: draft plan

This is a draft to start `/wf-plan` from. Nothing here has been applied, and the boot config change
is shown only as a diff. The pass mark is a proposal: under 10 µs residual bias after correction,
with jitter reported at p50, p99 and maximum. It does not need to be tighter, because the Pi clock is
not in the measurement timing chain. Camera stamps come from the Pico and IMU stamps from the
receiver, so the Pi clock serves only latency diagnostics and frame-to-trigger matching.

### Preflight, read-only

- Poll `MON-VER`, and save a `VALGET` snapshot of every layer. The SD logger depends on this receiver,
  so we need a way back.
- Find TIMEPULSE on the board and check its swing with the AD3 **before** connecting the Pi, outdoors
  with a fix. There is no pulse before time lock.

### Wiring

| Signal            | Connection                     | AD3                 |
| ----------------- | ------------------------------ | ------------------- |
| TIMEPULSE         | 1 kΩ series to GPIO18 (pin 12) | DIO0, at the Pi end |
| PPS echo          | GPIO17 (pin 11)                | DIO1                |
| System-clock edge | GPIO27 (pin 13)                | DIO2                |
| Ground            | Common, pin 9                  | GND                 |

### F9R config

Set by name via pyubx2, in RAM and BBR, with read-back.

| Key                                                                                | Value                   | Note                                               |
| ---------------------------------------------------------------------------------- | ----------------------- | -------------------------------------------------- |
| `CFG-TP-TIMEGRID_TP1`                                                              | 1 (GPS)                 | The only timepulse value that differs from default |
| `CFG-TP-TP1_ENA`, `SYNC_GNSS_TP1`, `USE_LOCKED_TP1`, `ALIGN_TO_TOW_TP1`, `POL_TP1` | 1                       | Rising edge at the top of the second               |
| `CFG-TP-PULSE_DEF` / `PULSE_LENGTH_DEF`                                            | 0 (PERIOD) / 1 (LENGTH) |                                                    |
| `CFG-TP-PERIOD_TP1` / `PERIOD_LOCK_TP1`                                            | 1000000 µs              |                                                    |
| `CFG-TP-LEN_TP1` / `LEN_LOCK_TP1`                                                  | 0 / 100000 µs           | No pulse until locked                              |
| `CFG-RATE-MEAS` / `RATE-NAV` / `RATE-TIMEREF`                                      | 1000 ms / 1 / GPS       | Keep 1 Hz for M1                                   |
| `CFG-MSGOUT-UBX_TIM_TP_USB`, `NAV_PVT_USB`, `NAV_TIMELS_USB`                       | 1                       |                                                    |
| `CFG-USBOUTPROT-NMEA`                                                              | 0                       | USB only; the logger's UART is untouched           |

Once M2 raises the rate, `trigger_bridge` must use the last `TIM-TP` before each edge.

### Boot config, not applied

```diff
 # /boot/firmware/config.txt, under [all]
+dtoverlay=pps-rp1,pin=18,pull-down,echo    # kernel >= 1:6.12.70-1+rpt1
+# otherwise: dtoverlay=pps-gpio,gpiopin=18  (no echo, so experiment B is skipped)
```

### Coarse time and chrony

A small host process, `host/ubx_mux`, owns the F9R port under either OS. It logs raw UBX, forwards
bytes to the ROS node, and feeds chrony only when `NAV-PVT` shows `validTime` and `fullyResolved`, so
time sync runs without ROS or a container. The SOCK message format comes from `refclock_sock.c` for
the installed chrony version.

```text
refclock SOCK /run/chrony.gnss.sock refid GNSS poll 2 delay 0.2 noselect
refclock PPS /dev/pps0 refid PPS lock GNSS poll 2 precision 1e-7 prefer
makestep 1 3
rtcsync
driftfile /var/lib/chrony/chrony.drift
log tracking refclocks statistics
logdir /var/log/chrony    # moves to the data partition in M5
```

### AD3 measurements

The AD3 buffers 32,768 samples per channel, so these run as one triggered capture per PPS: at
100 MS/s the window is about 328 µs, centred on the edge. Experiment A is the exception.

| Experiment      | Measures                                | Method                                                                                                                                                                                   |
| --------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A: reference    | AD3 clock error, pulse period and width | Stream at about 10 MS/s for at least 10 minutes and average periods. Reject runs with lost samples. Log `TIM-TP` `qErr` alongside.                                                       |
| B: echo         | PPS to kernel echo latency              | TIMEPULSE rise to GPIO17 rise. Check that chrony does not clear the echo setting.                                                                                                        |
| C: system clock | True clock error against GPS            | A pinned `SCHED_FIFO` process spins until `CLOCK_REALTIME` reads k+0.1 s, then toggles GPIO27 via `/dev/gpiomem0`. The AD3 compares that with the TIMEPULSE **falling** edge at k+0.1 s. |
| D: conditions   | What moves the bias                     | Repeat B and C for RP1 L1 on and off, default and `performance` governor, idle and loaded, 1 hour each, logging temperature.                                                             |

Experiment C uses the falling edge because activity on RP1 near the PPS changes the latency being
measured, and the short interval makes AD3 clock error negligible. A dummy RP1 read just before the
toggle keeps L1 wake-up out of the result. To check the sign of chrony's `offset`, set it from
experiment C and rerun: the error should shrink towards 0, and if it doubles the sign is wrong.
