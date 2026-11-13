# Where the user stands with hardware

The user is a navigation and state-estimation engineer, fluent in factor graphs, IMU and RF fusion,
ROS 2, C++ and Python. The fusion box is their first embedded project. Read this before explaining
anything, planning a probe or writing one up, and add to it whenever an entry shows something new
about what they know or don't know yet. Record what they demonstrated, with the entry it came from,
not what an engineer with their title would be expected to know.

## How to use it

- **Skip the basics of estimation, software and ROS 2.** Explain the basics of hardware, embedded
  protocols and Linux devices when they come up, briefly and once, with the check that confirms
  them on this hardware.
- **Ask for pasted output, never a retyped reading.** A reading copied by hand has already gone
  wrong once.
- **Write probes as labs.** Say what to check, why it matters and where it fits, how it is done
  and what it taught, so that each one can be followed again.

## Log

### rtk-inspection (2026-11-13)

Demonstrated, from the story of a first attempt months earlier and from this probe:

- They worked from a product page to the hookup guide, a sibling board's guide, and u-blox's
  integration manual and interface description, and picked out time tagging as something that would
  matter later.
- They configured UART1 output in u-center 2, checked it through an FTDI USB-serial adapter in
  picocom, and logged it with a SparkFun OpenLog.
- They wired a UART (TX, RX, 5 V, ground) to that logger.
- They ran and extended a short pyubx2 script against the receiver.

New to them, or not yet familiar:

- **USB serial on Linux.** They didn't know what CDC-ACM is, why the receiver appears as
  `/dev/ttyACM*`, or how that differs from a bridge chip on `/dev/ttyUSB*`.
- **Serial terminals.** They remembered picocom only by its unusual exit key, and asked how it
  relates to serial ports at all.
- **Per-port configuration.** They expected UBX on USB, having forgotten that their own earlier
  configuration put it on UART1. They didn't know that each port has its own output protocols and
  message rates.
- **Binary protocol framing.** They had not decoded a UBX frame (sync, class, ID, length,
  checksum) by hand before this probe.
- **Configuration layers.** RAM, BBR and flash, and what survives a power cycle, were new.
- **Records.** They didn't note the dates, durations or antenna state of their old recordings, and
  their first copy of `MON-VER` was retyped, with one character wrong.
- **Board-level details.** Their notes came from a sibling board's guide, and they hadn't yet
  checked this board's own silkscreen or the IOREF level the UART pins run at.
