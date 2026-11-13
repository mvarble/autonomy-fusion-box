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

Demonstrated in this probe:

- They worked from a product page to the hookup guide, a sibling board's guide, and u-blox's
  integration manual and interface description, and picked out time tagging as something that would
  matter later.
- They configured UART1 output in u-center 2, by key, and saved the configuration: UBX on and NMEA
  off on UART1, 115200 baud, `ESF-RAW` on UART1 and NAV2 output, each written to RAM, BBR and
  flash. They checked it through an FTDI USB-serial adapter in picocom, and logged it with a
  SparkFun OpenLog at the matching baud rate.
- They wired a UART (TX, RX, 5 V, ground) to that logger.
- They ran and extended a short pyubx2 script against the receiver.

New to them, or not yet familiar:

- **USB serial on Linux.** They didn't know what CDC-ACM is, why the receiver appears as
  `/dev/ttyACM*`, or how that differs from a bridge chip on `/dev/ttyUSB*`.
- **UART basics.** At the start they didn't know what a baud rate was or which settings a UART has,
  and chose u-center 2's GUI to discover them rather than reading the protocol first.
- **Serial terminals.** They remembered picocom only by its unusual exit key, and asked how it
  relates to serial ports at all.
- **Per-port configuration.** They had set it per port themselves, but months later expected UBX
  on USB. The model, that each port has its own output protocols and message rates, hadn't stuck.
- **Binary protocol framing.** They had not decoded a UBX frame (sync, class, ID, length,
  checksum) by hand before this probe.
- **Configuration layers.** They wrote to RAM, BBR and flash in u-center, but what each layer
  keeps across a power cycle, and that this board has no backup supply for BBR, were new. The box
  writes RAM and BBR only, so flash writes need their explicit approval.
- **Records.** They didn't note the dates, durations or antenna state of their old recordings, and
  their first copy of `MON-VER` was retyped, with one character wrong.
- **Board-level details.** Their notes came from a sibling board's guide, and they hadn't yet
  checked this board's own silkscreen or the IOREF level the UART pins run at.
