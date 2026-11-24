---
summary: The box has no separate SD logger; the Pi reaches the receiver over USB alone, with UART1's output turned off, and records everything, the raw IMU and GNSS observations included, into its bags and a raw host log on its microSD, until a measurement says the card cannot keep up.
---

## Context

The plan had two recorders.
The Pi records the bags, and a separate SD-card logger on one of the receiver's UARTs kept an independent copy of the raw UBX stream, for PPK ground truth with RTKLIB ([what the box is](../../start/what-the-box-is/)).
The [rtk-inspection](../rtk-inspection/measure.md) lab used a SparkFun OpenLog in that role, on UART1.

Two recorders mean two wirings, two port configurations and two files to line up afterwards.
They also left a question in the ledger, [#14](../../reference/open-questions/#blocking-m2), whether the logger and the Pi conflict on the receiver's ports.
Meanwhile the [foundations](../foundations/writeup.md) entry had already given the Pi its own path to the receiver: `host/ubx_mux` owns the receiver's USB port, feeds chrony and forwards bytes to the ROS driver, and the [M1 draft plan](../../reference/milestones/#m1-draft-plan) has it log the raw UBX stream as well.
The logger only duplicates that log, from a different port, on a card with no clock.

## Decision

**There is no separate logger.**
The Pi records everything: the bags, and the raw UBX stream that PPK needs.
The reason is simplicity: one recorder, one wiring and one receiver configuration to reason about, test and keep true.

**The receiver reaches the Pi over USB alone.**
The USB cable already carries the receiver's power from the Pi, and `ubx_mux` already owns its port, so data takes the same cable.
UART1 is not wired to anything in the box, and its output is turned off.

UART1 would also be the weaker path.
The lab measured 6 586 to 6 728 bytes a second on UART1 carrying `ESF-RAW` alone ([rtk-inspection, Results](../rtk-inspection/measure.md#results)).
At 115200 baud, with ten bits on the wire for each byte, the line carries at most 11 520 bytes a second, so the IMU stream alone fills more than half of it before the raw GNSS observations or `NAV-PVT` are added.
It is also the port on which frames arrived cut short ([#32](../../reference/open-questions/#blocking-m2)).

A second, redundant path over UART1 was weighed and loses on the same ground.
Power and data share the USB cable, so the failure it guards against is narrow: the receiver powered and running while the Pi's side of USB, or `ubx_mux`, fails.
Against that it costs a second reader, a second port configuration and a second file to reconcile.

**The bags carry the raw observations.**
The receiver sends `ESF-RAW`, `RXM-RAWX` and `RXM-SFRBX` on USB, and the UBX driver publishes each as a message that keeps its fields as the receiver sent them, beside the stamping fields every message has.
The bags are the datasets that fusion algorithms are explored on later, so they hold what the receiver measured, not only what it solved: the IMU's samples and the GNSS observations as well as `NAV-PVT`.
A filter written later can then be run against a recording made now.

These messages obey the stamping rule like any other.
For `RXM-RAWX` the measurement time is in the message.
For `ESF-RAW` it is not: its `sTtag` has no documented mapping to GNSS time ([#10](../../reference/open-questions/#blocking-m2)), so the IMU's `header.stamp` cannot be set at the source until #10 is closed.
Until then the bags keep `sTtag` raw, and IMU messages are not trusted for timing.

**`ubx_mux` also writes the raw byte stream to a file** on the data partition, as it receives it and outside ROS, as the M1 draft plan already has it do.
That file is what RTKLIB reads for PPK, without a conversion out of the bags, and it survives a crash of the ROS graph, though not a failure of the Pi or its card.
It is also the check on the bags: every message the driver published can be found, byte for byte, in the file.

**UART1's output is turned off.**
The lab left UBX output and `ESF-RAW` enabled on UART1, written to RAM, BBR and flash.
The box's startup configuration turns UART1's UBX output off in RAM and BBR, so that the receiver sends only what the box records.
Flash is left as the lab wrote it: this decision needs no flash write, and at every power-up the startup configuration overrides it.

The keys for all of this are set by name with `VALSET` and confirmed with `VALGET`, in RAM and BBR, once `UBX-MON-VER` has said which keys the firmware has; the M2 plan names them.

**The data is written to the Pi's microSD**, on the data partition M5 already plans, with the OS on the same card.
That card has to take the camera's frames as well as the UBX stream, and the camera's frame rate and bit depth are not decided yet.
Whether a microSD keeps up with that, sustained, and beside the OS, is a fact about this card, so it becomes a ledger row closed by measurement inside M5.
If it fails, a later entry moves the data partition to a separate drive and revises this one.

## Consequences

- The receiver has one data path, so the M2 configuration has one port to send on and one to switch off, and #14 has nothing left to ask: it is settled as DECIDED by this entry.
- The one raw record lives where every other stream lives, on a timebase the Pi can stamp, instead of on a card with no clock.
- A recording is a dataset: the raw IMU and GNSS observations sit in the same bag as the camera's frames, on the same timebase.
- The bags grow by the raw observations' rate, on a card already carrying the camera's frames, which the microSD row below has to include.
- There is no record independent of the Pi.
  A dead card, a failed boot or a power cut mid-write loses the raw UBX stream along with everything else.
  M5's read-only root, data partition and bag splitting are what limit that loss, and they become the only protection.
- #32 stays open but changes what it blocks.
  The box no longer records from UART1, so the question for M2 is whether the USB log shows the same mid-frame losses; the raw log's checksums answer that, and only if they do is the cause worth chasing on UART1.
- The ledger gains rows for what the decision rests on and has not been checked: that the receiver's firmware sends `RXM-RAWX` and `RXM-SFRBX` on USB, and that the microSD sustains the recorder's write rate.
- The pages that show the logger change: the hardware table and the box's diagram, and the M1 draft's notes that the SD logger depends on the receiver and that its UART is untouched.
  The rtk-inspection lab keeps everything it recorded; only its reference to #14 is kept true, as an amendment at publish.
- The OpenLog stays a bench tool: it recorded UART1 once without a computer, and can again.

## Alternatives

- **Keep the logger as an independent backup.**
  It is the only option that survives a failure of the Pi.
  It lost because the backup it gives is weak and costly: it has no clock, it lost frames as the FTDI path did, it needs its own UART configuration on a port already half full with the IMU alone, and its file has to be aligned to the Pi's afterwards.
- **Feed the Pi from UART1 instead of USB.**
  The receiver would still need USB, or another supply, for power, and UART1 is the narrower and so far lossier port.
- **The raw observations in the host file only.**
  It keeps one copy, but leaves the bags without the measurements a fusion algorithm needs, so every later experiment would first have to merge the file back into the bags.
- **Both USB and UART1 into the Pi.**
  Redundant against a failure on the Pi's side of USB only, at the cost of a second reader and a second configuration.
- **Record to a USB SSD or an NVMe drive now.**
  It would likely remove the throughput and wear risk, but it adds hardware, power draw on a 5 V, 3 A budget that is itself unmeasured ([#27](../../reference/open-questions/#blocking-m7)), and a mount to the case, before any measurement says the microSD is not enough.
