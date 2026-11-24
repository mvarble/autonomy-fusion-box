---
summary: The box has no separate SD logger; everything, the raw UBX stream for PPK included, is recorded on the Pi, which reaches the receiver over USB alone, and the Pi's microSD holds the data until a measurement says it cannot.
---

## Context

The plan had two recorders.
The Pi records the bags, and a separate SD-card logger on one of the receiver's UARTs kept an independent copy of the raw UBX stream, for PPK ground truth with RTKLIB ([what the box is](../../start/what-the-box-is/)).
The [rtk-inspection](../rtk-inspection/measure.md) lab used a SparkFun OpenLog in that role, on UART1.

Two recorders mean two wirings, two port configurations and two files to line up afterwards.
They also left a question in the ledger, [#14](../../reference/open-questions/#blocking-m2), whether the logger and the Pi conflict on the receiver's ports.
Meanwhile the [foundations](../foundations/writeup.md) entry had already given the Pi its own path to the receiver: `host/ubx_mux` owns the receiver's USB port, logs the raw UBX stream, feeds chrony and forwards bytes to the ROS driver.
The logger only duplicates that log, from a different port, on a card with no clock.

## Decision

**There is no separate logger.**
The Pi records everything: the bags, and the raw UBX stream that PPK needs.
The reason is simplicity: one recorder, one wiring and one receiver configuration to reason about, test and keep true.

**The receiver reaches the Pi over USB alone.**
The USB cable already carries the receiver's power from the Pi, and `ubx_mux` already owns its port, so data takes the same cable.
UART1 is not wired to anything in the box.

UART1 would also be the weaker path.
The lab measured 6 586 to 6 728 bytes a second on UART1 carrying `ESF-RAW` alone ([rtk-inspection, Results](../rtk-inspection/measure.md#results)).
At 115200 baud, with ten bits on the wire for each byte, the line carries at most 11 520 bytes a second, so the IMU stream alone fills more than half of it before the raw GNSS observations or `NAV-PVT` are added.
It is also the port on which frames arrived cut short ([#32](../../reference/open-questions/#blocking-m2)).

A second, redundant path over UART1 was weighed and loses on the same ground.
Power and data share the USB cable, so the failure it guards against is narrow: the receiver powered and running while the Pi's side of USB, or `ubx_mux`, fails.
Against that it costs a second reader, a second port configuration and a second file to reconcile.

**PPK's raw observations come from `ubx_mux`'s host log.**
The receiver sends `RXM-RAWX` and `RXM-SFRBX` on USB, and `ubx_mux` writes the raw byte stream to a file on the data partition, as it receives it and outside ROS.
That record survives a crash of the ROS graph, though not a failure of the Pi or its card.
The keys are set by name with `VALSET` and confirmed with `VALGET`, in RAM and BBR, once `UBX-MON-VER` has said which keys the firmware has; the M2 plan names them.

> [!TODO] Confirm the PPK source
> The position above takes the host log as the one raw record.
> Whether the UBX driver should also publish `RXM-RAWX` and `RXM-SFRBX` into the bags, for convenience, is open.
> I would not: the host file is what RTKLIB reads, and a second copy in the bags is a second thing to keep in step.

> [!TODO] UART1's output
> The lab left UBX output and `ESF-RAW` enabled on UART1, written to RAM, BBR and flash.
> With nothing wired to it, that output is harmless to the box, but it is traffic the receiver still generates.
> I would have the box's startup configuration turn UART1's UBX output off in RAM and BBR, with read-back, so that the receiver sends only what the box records, and leave flash alone: no flash write is needed for this decision.
> The alternative is to leave UART1 as the lab left it.

**The data is written to the Pi's microSD**, on the data partition M5 already plans, with the OS on the same card.
That card has to take the camera's frames as well as the UBX stream, and the camera's frame rate and bit depth are not decided yet.
Whether a microSD keeps up with that, sustained, and beside the OS, is a fact about this card, so it becomes a ledger row closed by measurement inside M5.
If it fails, a later entry moves the data partition to a separate drive and revises this one.

## Consequences

- The receiver has one data path, so the M2 configuration has one port to set and read back, and #14 has nothing left to ask: it is settled as DECIDED by this entry.
- The one raw record lives where every other stream lives, on a timebase the Pi can stamp, instead of on a card with no clock.
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
- **Both USB and UART1 into the Pi.**
  Redundant against a failure on the Pi's side of USB only, at the cost of a second reader and a second configuration.
- **Record to a USB SSD or an NVMe drive now.**
  It would likely remove the throughput and wear risk, but it adds hardware, power draw on a 5 V, 3 A budget that is itself unmeasured ([#27](../../reference/open-questions/#blocking-m7)), and a mount to the case, before any measurement says the microSD is not enough.
