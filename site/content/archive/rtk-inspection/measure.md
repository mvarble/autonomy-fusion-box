---
summary: A first session with the ArduSimple ZED-F9R board. It reads the firmware (HPS 1.40, protocol 33.40) over USB, reads the board's silkscreen, and decodes old OpenLog recordings of the IMU, which give `ESF-RAW`'s framing (one 7-sample set per message, 257 time-tag ticks apart) but not yet its rate in Hz.
---

<script>
	import board from './board.jpg';
	import rails from './ardusimple-arduino-rails.jpg';
	import timeTagging from './im-esf-meas-time-tagging.png';
	import esfRaw from './id-esf-raw.png';
</script>

Before the box can configure the receiver, stamp its data or decode its IMU, it has to know what is
actually on the bench. This lab is a first session with the ArduSimple ZED-F9R board. It runs four
checks, each small enough for an afternoon:

1. [how the receiver appears to Linux over USB](#1-how-the-receiver-appears-over-usb);
2. [which firmware it runs](#2-which-firmware-the-receiver-runs);
3. [what the board itself says](#3-what-the-board-says), read from its silkscreen;
4. [what its IMU stream looks like](#4-what-the-imu-stream-looks-like), from recordings made long
   ago with an SD-card logger.

Before them comes [the story](#before-this-lab-a-first-attempt-months-ago) of a first attempt
with the same board, months earlier, which left it wired the way this lab found it.

Each check follows the same pattern: what to check, why it matters and where it fits in the box,
how it is done, what came out, and what it taught. Two ledger questions are the targets:
[#1](../../reference/open-questions/index.md#blocking-m1), the firmware, and
[#11](../../reference/open-questions/index.md#blocking-m2), the IMU's rate and framing. The checks
also turn up facts for several others, collected in [What it closes](#what-it-closes).

Two vendor documents carry most of the weight, and their exact revisions matter, because sections
move between revisions:

- `[ID]` is the u-blox F9 HPS 1.30 Interface Description, UBX-22010984 R03. It defines every UBX
  message and configuration key.
- `[IM]` is the ZED-F9R Integration Manual, UBX-20039643. Its URL in the ledger served revision
  R10 on 2026-11-13. It explains how the receiver behaves.

Every check that talks to the receiver here only reads from it. None changes its configuration.

## Before this lab: a first attempt, months ago

This board did not arrive fresh for this lab. Months earlier, before the box was an idea, I had
tried to get GPS, IMU and INS estimates out of it, simply to log all sorts of useful data and look
at it. I never got as far as looking. This project replaced that plan. What follows is what I did
then, reconstructed from memory. It is the reason the board has four wires on it, and it explains
some of what the checks below found.

**Finding the documentation.** I started at the
[product page](https://www.ardusimple.com/product/simplertk2b-fusion/) for the simpleRTK2B Fusion,
which led to its
[hookup guide](https://www.ardusimple.com/rtk-ins-simplertk2b-f9r-hookup-guide/). The general
material about pins was not there. It was in the
[guide for a sibling board](https://www.ardusimple.com/user-guide-simplertk2b-budget/), the
simpleRTK2B Budget, which carries a ZED-F9P rather than the F9R. Its section on the
[Arduino rails](https://www.ardusimple.com/user-guide-simplertk2b-budget/#arduino) showed which
header pins carry which UART:

<figure>
	<img src={rails} alt="ArduSimple's user guide for the simpleRTK2B Budget, section Arduino rails: a photo of the board with the header pins highlighted, and a list. GND should always be connected. 5V_IN can power the board, with the 5V switch set to input. IOREF is an input that sets the voltage level of the next pins, from 1.2 V to 5.5 V. TX1 and RX1 are ZED-F9P UART1 TX and RX. TX2 and RX2 are the XBee UART, also connected to the ZED-F9P's UART2. Connecting your own hardware to UART1 or UART2 makes it mandatory to connect IOREF to the voltage your hardware needs." width="826" height="1011" />
	<figcaption>The Arduino rails, from ArduSimple's guide to the simpleRTK2B Budget, a sibling board with a ZED-F9P. Screenshot of <a href="https://www.ardusimple.com/user-guide-simplertk2b-budget/#arduino">the guide</a>.</figcaption>
</figure>

That guide also pointed to u-center 2, u-blox's configuration tool. At the bottom of the hookup
guide was u-blox's own
[getting-started note for the ZED-F9R](https://content.u-blox.com/sites/default/files/documents/ZED-F9R-GettingStarted_AppNote_UBX-22035176.pdf),
and from there the two documents this lab leans on. In the
[integration manual](https://www.u-blox.com/docs/UBX-20039643), a search for "IMU" turned up the
section on time tagging. I didn't need it then, but I could tell that time would matter:

<figure>
	<img src={timeTagging} alt="ZED-F9R Integration Manual section 3.2.5.2, UBX-ESF-MEAS time tagging. The epoch of sensor data can be taken from the reception time of the message's first byte or from a time mark on an external input. Latency is configurable per sensor. Time tags for all UBX-ESF-MEAS data must have the same resolution, and the receiver generates ESF-MEAS from its internal IMU with a default time tag resolution of 1 millisecond." width="847" height="422" />
	<figcaption>Integration manual §3.2.5.2, on time-tagging sensor data. Screenshot of <a href="https://www.u-blox.com/docs/UBX-20039643">the manual</a>.</figcaption>
</figure>

The [interface description](https://www.u-blox.com/docs/UBX-22010984) showed how much of the
receiver lives in UBX messages, each with a class, an ID and a fixed layout, like `ESF-RAW`:

<figure>
	<img src={esfRaw} alt="u-blox interface description section 3.11.4, UBX-ESF-RAW (0x10 0x03), raw sensor measurements. Output message, length 4 + n times 8 bytes. Payload: a 4-byte reserved0 field, then a repeated group of a 4-byte data field, whose bits 23 to 0 are dataField and bits 31 to 24 dataType, and a 4-byte sTtag, the sensor time tag." width="862" height="490" />
	<figcaption>Interface description §3.11.4, <code>UBX-ESF-RAW</code>. Screenshot of <a href="https://www.u-blox.com/docs/UBX-22010984">the interface description</a>.</figcaption>
</figure>

**Configuring and logging.** I ran u-center 2 on Windows and configured the receiver to send the
messages I wanted to parse and interpret out of UART1. To check that something came out, I
connected the UART1 pins to an FTDI USB-serial adapter and watched the bytes arrive in picocom on
Linux. Then I swapped the adapter for a SparkFun OpenLog, which wrote UART1 to an SD card.

**In hindsight**, each step of that attempt matches something the checks below came back to:

- **The FTDI adapter** is the other kind of USB serial port, a bridge chip on `/dev/ttyUSB*`.
  [Check 1](#1-how-the-receiver-appears-over-usb) contrasts it with the F9R's own USB.
- **Configuring UART1 rather than USB** is why USB carries only NMEA today, in
  [check 2](#2-which-firmware-the-receiver-runs).
- **The Budget guide is for a different board.** [Check 3](#3-what-the-board-says) reads this
  board's own silkscreen. Its rule about IOREF matters: that pin sets the UART's voltage level, so
  it has to match whatever is connected, and the Pi's GPIOs are not 5 V tolerant `[RPI-HW]`.
- **The time-tagging section** describes `ESF-MEAS`, whose time tags have a 1 ms resolution.
  [Check 4](#4-what-the-imu-stream-looks-like) shows that this does not carry over to
  `ESF-RAW`.
- **The OpenLog's files** are what check 4 decodes.

## The setup

<figure>
	<img src={board} alt="The ArduSimple board in a black enclosure, with a red, a blue, a yellow and a green wire on its headers, leaving through the enclosure wall. The u-blox ZED-F9R module sits at the lower right, beside the SMA antenna connector." width="1444" height="1362" />
	<figcaption>The board as probed. The F9R module is at the lower right, next to the SMA antenna connector and the POWER + GPS USB-C port.</figcaption>
</figure>

The board sits in a 3D-printed enclosure and is powered over USB. The enclosure is a
design I found online, [on Thingiverse](https://www.thingiverse.com/thing:3551604), and the Santa
Barbara Public Library printed it for me, for free. A public library is worth asking before buying
a printer for one part. The four coloured wires are left
over from [the first attempt](#before-this-lab-a-first-attempt-months-ago). They run to the
SparkFun OpenLog, and they were left in place for this lab.

The host is my desktop computer, running Arch Linux, kernel 7.2.14-arch1-1. The scripts run from the Pixi
environment at the repository root: Python 3.15.2, pyubx2 1.4.1 and pyserial 3.5. A Windows
install of u-center 2, u-blox's own tool, served as a cross-check.

## 1. How the receiver appears over USB

**What to check.** When the board is plugged in, which device file appears, which kernel driver
handles it, and whether there is anything between the F9R and the USB cable.

**Why it matters.** Everything the box sends to and reads from the receiver goes through this
port. The host process that will own it ([#5](../../reference/open-questions/index.md#blocking-m1))
needs a name for it that survives reboots and replugging, and permission to open it. Two very
different things can sit behind a USB serial port. One is the receiver's own USB. The other is a
USB-to-UART bridge chip wired to one of its UART pins, which brings its own baud rate, its own
buffering and its own latency.

**How it is done.** Linux has two conventions for serial ports over USB, and the device name tells
them apart.

- **`/dev/ttyACM*`** comes from the `cdc_acm` driver. It binds to any device whose interface
  declares USB class 02 (Communications), subclass 02 (Abstract Control Model), the standard USB
  class for a serial device. It matches on the class, not on a vendor, so no vendor driver is
  needed. Because the class was designed for modems, desktop services such as ModemManager may
  probe a new `ttyACM` device, and on the Pi it is worth telling them to leave it alone.
- **`/dev/ttyUSB*`** comes from the `usbserial` family of drivers for bridge chips (FTDI, CP210x,
  CH340). These match on vendor and product IDs.

The numbers in either name follow the order in which devices appear, so they are not stable. udev
adds stable links under `/dev/serial/by-id/`, built from the device's vendor, product and serial
strings.

The board has two USB-C ports, labelled POWER + XBEE and POWER + GPS. The cable went to POWER +
GPS, next to the antenna connector. The kernel log as it was plugged in, and udev's view of the
device, can both be read without touching the receiver:

```sh
journalctl -k -b | grep -iE 'cdc_acm|ttyACM|1546'
udevadm info -q property -n /dev/ttyACM0
ls -l /dev/serial/by-id/
```

**What came out.**

```text
usb 1-1.1.3: New USB device found, idVendor=1546, idProduct=01a9, bcdDevice= 1.00
cdc_acm 1-1.1.3:1.0: ttyACM0: USB ACM device
```

- **Vendor:** `1546` is u-blox.
- **Interfaces:** udev lists them as `:020201:0a00ff:`. That is a communications interface (class
  02, subclass 02, protocol 01) and a CDC data interface (class 0a), which carries the bytes.
- **Stable name:** `/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_GNSS_receiver-if00`.
- **Permissions:** the device node belongs to group `uucp`.

**What I learned.**
- **POWER + GPS is the F9R's native USB**, with no bridge chip in between. So its "baud rate" is a
  formality: a CDC-ACM device receives it as a USB request and is free to ignore it.
- **Configure the box with the `by-id` name, never `ttyACM0`.** The name carries no serial number,
  though, so a second u-blox device on the same host would get the same one.
- **On the Pi**, the host process's user needs group `uucp`, or a udev rule.

## 2. Which firmware the receiver runs

**What to check.** The receiver's firmware and protocol versions, as the receiver itself reports
them in `UBX-MON-VER`.

**Why it matters.** This is [#1](../../reference/open-questions/index.md#blocking-m1), and the
first fact M1 builds on. The configuration keys the box will set, the UBX messages that exist and
their layouts all depend on the firmware. Some behaviour does too: UBX output on UART2, for
example, exists only from HPS 1.30 `[IM §3.1.3]`. The config tool will set keys by name with
`VALSET` and read them back with `VALGET`, against the interface description for this firmware,
and it will check `MON-VER` on every start before it does anything else.

**How it is done.** UBX is u-blox's binary protocol. Every frame has the same shape:

| bytes   | content                                                               |
| ------- | --------------------------------------------------------------------- |
| 2       | sync, `b5 62`                                                         |
| 1 + 1   | message class and ID                                                  |
| 2       | payload length, little-endian                                         |
| n       | payload                                                               |
| 2       | checksum: an 8-bit Fletcher sum over class, ID, length and payload    |

To *poll* a message, the host sends that message with an empty payload, and the receiver answers
with the full message. A `MON-VER` poll is 8 bytes, `b5 62 0a 04 00 00 0e 34`, and changes
nothing on the receiver. The script sends it and prints the reply both as raw hex and parsed:

```python
# tools/get-firmware.py
import sys

import serial
from pyubx2 import POLL, UBXMessage, UBXReader

with serial.Serial(sys.argv[1], 38400, timeout=3) as s:  # baud is ignored on USB CDC
    s.write(UBXMessage("MON", "MON-VER", POLL).serialize())
    for raw, msg in UBXReader(s, protfilter=2):  # UBX only
        if msg.identity == "MON-VER":
            print(raw.hex())
            print(msg)
            break
```

It runs as `pixi run get-firmware /dev/ttyACM0`. The same USB port also streams NMEA text, and
`protfilter=2` makes the reader skip it so the reply is not lost among the sentences. I ran it many
times without keeping count. u-center 2 on Windows, polling the same message, gave the
cross-check.

**What came out.** The reply, exactly as printed (228 bytes):

```text
b5620a04dc0045585420434f524520312e3030202866386239303129000000000000000030303139303030300000524f4d20424153452030783131384232303630000000000000000000000046575645523d48505320312e34300000000000000000000000000000000050524f545645523d33332e343000000000000000000000000000000000004d4f443d5a45442d463952000000000000000000000000000000000000004750533b474c4f3b47414c3b424453000000000000000000000000000000534241533b515a535300000000000000000000000000000000000000000006f1
```

It is worth decoding one frame by hand, because every later UBX bug is easier to find for having
done it once:

- `b5 62` is the sync, and `0a 04` is the class and ID of `MON-VER`.
- `dc 00` is the payload length, little-endian: 220 bytes. That matches the bytes received, and
  fits a 30-byte `swVersion`, a 10-byte `hwVersion` and six 30-byte extensions
  (30 + 10 + 6 × 30 = 220).
- The checksum over class, ID, length and payload comes out to `06 f1`, the last two bytes
  received.

Each field is NUL-padded ASCII, so the version can even be read straight off a hex dump:

| field       | value                    |
| ----------- | ------------------------ |
| `swVersion` | `EXT CORE 1.00 (f8b901)` |
| `hwVersion` | `00190000`               |
| extension 1 | `ROM BASE 0x118B2060`    |
| extension 2 | `FWVER=HPS 1.40`         |
| extension 3 | `PROTVER=33.40`          |
| extension 4 | `MOD=ZED-F9R`            |
| extension 5 | `GPS;GLO;GAL;BDS`        |
| extension 6 | `SBAS;QZSS`              |

u-center 2 reported the same value in every field.

**What I learned.**
- **The receiver runs HPS 1.40, protocol 33.40.** The interface description in the ledger, `[ID]`,
  is the HPS 1.30 one. So every key and message the box uses has to be checked against the HPS 1.40
  edition before M1 relies on it. HPS 1.40 does meet the "HPS 1.30 or later" condition for UBX
  output on UART2 `[IM §3.1.3]`.
- **The firmware has been updated since the module was made.** The module is marked
  `ZED-F9R-01B-00`, and `[IM]`'s list of products gives that type HPS 1.20. HPS 1.40 belongs to
  `ZED-F9R-04B-00` in the same list. So the module's marking says nothing reliable about its
  firmware, and `MON-VER` is the only way to know.
- **The version is one 8-byte poll away, from any host, with no vendor tool.**
- **USB and the UART pins are configured separately.** Opening the USB port in picocom, a minimal
  serial terminal, showed NMEA sentences and no UBX. That is not a fault. Each port has its own
  output protocols and its own rate for each message. This board's UBX output had been set up on
  UART1, for the logger, and USB had been left with the default NMEA output. A binary UBX frame
  would barely show in a terminal anyway: a stray `µb`, then control characters.

## 3. What the board says

**What to check.** Read the board itself: which pins carry which signals, how the switches are set,
which LEDs are lit, and what is fitted.

**Why it matters.** The box will wire the F9R's timepulse to the Pi's PPS input and a UART to the
Pi. A wrong pin is at best a silent input and at worst a damaged GPIO, since the Pi's GPIOs are not
5 V tolerant `[RPI-HW]` (see the ledger's sources). The silkscreen is the cheapest evidence there is, and it is the first step of
[#2](../../reference/open-questions/index.md#blocking-m1), where TIMEPULSE and EXTINT are on this
board. Product pages and hookup guides often describe another revision of the board.

**How it is done.** From the photo above, enlarged where the labels are small.

**What came out.**

- **The module** is marked `ZED-F9R-01B-00`.
- **The wires**, all four leaving through the enclosure wall to the OpenLog:
  - **yellow:** `TX1`, on the bottom header;
  - **green:** `RX1`, beside it;
  - **red:** 5 V, at the top header's pin above `LED7` (`5V IN/OUT`);
  - **blue:** ground, at the end of the XBee socket's lower row.
- **J4, a 6-pin JST connector labelled PIXHAWK + POWER**, is at the right edge. Its pins read, from
  1 to 6: `VIN`, `RX1`, `TX1`, `TPS`, `EVT`, `GND`.
- **The bottom header** also carries `RX2`, `TX2`, `GEOFENCE`, `EXTINT`, `TPS`, `GND`, `RST`,
  `SDA` and `SCL`. A separate `TPS` pad, labelled `J9`, sits near the top.
- **A slide switch labelled XBEE TO GPS UART1 / XBEE TO GPS UART2** picks which of the F9R's UARTs
  the XBee socket reaches. It is set to UART2, and the socket is empty.
- **A second slide switch** chooses between `IOREF = 3V3, 5V = OUTPUT` and
  `IOREF & 5V ARE INPUTS`.
- **The footprint labelled `BAT`**, a circle with two pads in the middle of the board, has nothing
  fitted.
- **LEDs:** `POWER` is lit, and so is `NO RTK`, in red. `PVT` is dark, and the photo was taken
  indoors. `5V IN/OUT`, `IOREF` and one of the `GPS>XBEE` / `XBEE>GPS` pair are lit too.

The OpenLog's `config.txt`, verbatim:

```text
115200,26,3,0,1,1,0
baud,escape,esc#,mode,verb,echo,ignoreRX
```

**What I learned.**
- **The timepulse is on at least three places**, all labelled `TPS`: J4, the bottom header and the
  `J9` pad. An event input is on J4 (`EVT`) and the header (`EXTINT`). Which one the Pi should use,
  and whether it is clean there, is for the AD3 to say in #2 and #3. The labels only say where to
  put the probe.
- **UART1 is shared.** It is on J4 and on the bottom header, and as found it fed the OpenLog at
  115200 baud. The default is 38400 `[IM §3.1.3]`, so the old configuration changed it. UART2 went
  to the empty XBee socket. That is the shape [#14](../../reference/open-questions/index.md#blocking-m2)
  asks about.
- **Green carries the OpenLog's output into the F9R's `RX1`.** Whatever the OpenLog transmits
  arrives at the receiver's UART1 input. If UART1 goes to the Pi, that wire comes off first.
- **The old configuration is most likely in flash.** RAM settings are lost at power-off, and BBR
  keeps them only while a backup supply holds `[IM §3.1]`. The `BAT` footprint has nothing fitted,
  yet UBX still comes out of UART1. A `VALGET` of each layer would settle it, which is
  [#9](../../reference/open-questions/index.md#blocking-m1). Before the box changes anything, those
  stored layers should be read back and recorded, so that what the board held before is known.

## 4. What the IMU stream looks like

**What to check.** How `UBX-ESF-RAW`, the message that carries the F9R's raw IMU samples, frames
them, and at what rate it comes.

**Why it matters.** This is [#11](../../reference/open-questions/index.md#blocking-m2), and it
shapes M2. The framing decides how the driver turns messages into `sensor_msgs/Imu`: one message
per sample, or samples matched up across messages. The rate decides the noise model's bandwidth,
the Allan variance's shortest averaging time and the size of a bag. The time tag, `sTtag`, is what
[#10](../../reference/open-questions/index.md#blocking-m2) must map to GNSS time, so how it
counts matters to the stamping rule.

**How it is done.** The OpenLog's SD card held four logs, `LOG00001.TXT` to `LOG00004.TXT`, from
the earlier setup. Each is exactly what UART1 sent, byte for byte, with no timestamps of the
OpenLog's own. When they were recorded and for how long is not known, and the GPS antenna was most
likely not connected for any of them.

pyubx2 1.4.1 recognises `ESF-RAW` but leaves its data words as raw bytes, so I wrote
`tools/ubx-dump.py`. It frames the byte stream itself, rather than trusting a parser to skip what
it does not understand. Every byte ends up counted as one of four things: a good UBX frame, a frame
with a bad checksum, an NMEA sentence, or a stray byte. A gap or a corrupt patch in a log therefore
shows up instead of vanishing. It decodes `ESF-RAW` from the documents:

- the payload is a 4-byte reserved field, then repeated 8-byte groups, each a data word and a U4
  `sTtag` (`[ID §3.11.4]`);
- in the data word, bits 23…0 are `dataField` and bits 31…24 are `dataType` (`[ID §3.11.4]`);
- the types, their scales and their signedness are in `[IM]` Table 15 (§3.2.7.5).

`pixi run python tools/ubx-dump.py FILE` prints every message, `--only ESF-RAW` filters, and
`--summary` prints the totals below. I ran `--summary` once on each log.

<details>
<summary><code>tools/ubx-dump.py</code>, in full</summary>

```python
"""Pretty-print, or summarise, the UBX messages in a byte stream recorded from an F9R port.

usage: ubx-dump.py FILE [--summary] [--only IDENTITY ...] [--limit N]

The file is whatever the port sent: an OpenLog `LOGnnnnn.TXT`, or any raw capture. The stream is
framed here, not by pyubx2, so that every byte is accounted for: UBX frames with a good checksum,
UBX frames with a bad one, NMEA sentences, and bytes that belong to neither. A gap in a log shows up
as bad frames or stray bytes rather than vanishing.

`UBX-ESF-RAW` is decoded here because pyubx2 leaves its data words as bytes. Layout from the u-blox F9
HPS 1.30 Interface Description (UBX-22010984 R03) §3.11.4: a 4-byte reserved field, then repeated
8-byte groups of `data` (bits 23..0 `dataField`, bits 31..24 `dataType`) and a U4 `sTtag`. Types,
scales and signedness from the ZED-F9R Integration Manual (UBX-20039643 R10) Table 15.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field

from pyubx2 import UBXReader

# dataType -> (name, unit, scale). Integration Manual R10 Table 15; all signed 24-bit.
ESF_TYPES: dict[int, tuple[str, str, float]] = {
    5: ("gyro_z", "deg/s", 2**-12),
    12: ("gyro_temp", "degC", 1e-2),
    13: ("gyro_y", "deg/s", 2**-12),
    14: ("gyro_x", "deg/s", 2**-12),
    16: ("accel_x", "m/s^2", 2**-10),
    17: ("accel_y", "m/s^2", 2**-10),
    18: ("accel_z", "m/s^2", 2**-10),
}


@dataclass
class Frame:
    offset: int
    kind: str  # "ubx", "ubx-bad-checksum", "nmea", "junk"
    data: bytes


def checksum(body: bytes) -> bytes:
    a = b = 0
    for x in body:
        a = (a + x) & 0xFF
        b = (b + a) & 0xFF
    return bytes((a, b))


def frames(buf: bytes) -> Iterator[Frame]:
    """Splits `buf` into UBX frames, NMEA sentences and leftover bytes, in order."""
    i, n, junk_start = 0, len(buf), None

    def flush(end: int) -> Iterator[Frame]:
        nonlocal junk_start
        if junk_start is not None and end > junk_start:
            yield Frame(junk_start, "junk", buf[junk_start:end])
        junk_start = None

    while i < n:
        if buf[i] == 0xB5 and i + 1 < n and buf[i + 1] == 0x62 and i + 6 <= n:
            length = int.from_bytes(buf[i + 4 : i + 6], "little")
            end = i + 6 + length + 2
            if end <= n:
                ok = checksum(buf[i + 2 : end - 2]) == buf[end - 2 : end]
                if ok:
                    yield from flush(i)
                    yield Frame(i, "ubx", buf[i:end])
                    i = end
                    continue
                # A bad checksum may be a corrupt frame or a false sync inside other data; report it
                # but resume one byte on, so a real frame that starts inside it is not lost.
                yield from flush(i)
                yield Frame(i, "ubx-bad-checksum", buf[i:end])
                i += 1
                continue
        if buf[i] == ord("$"):
            nl = buf.find(b"\n", i, i + 100)
            if nl != -1 and buf[i + 1 : i + 3].isalpha():
                yield from flush(i)
                yield Frame(i, "nmea", buf[i : nl + 1])
                i = nl + 1
                continue
        if junk_start is None:
            junk_start = i
        i += 1
    yield from flush(n)


@dataclass
class EsfRaw:
    reserved0: bytes
    samples: list[tuple[int, int, int]]  # (dataType, dataField, sTtag)


def decode_esf_raw(frame: bytes) -> EsfRaw:
    payload = frame[6:-2]
    samples = []
    for k in range(4, len(payload) - 7, 8):
        word = int.from_bytes(payload[k : k + 4], "little")
        value = word & 0xFFFFFF
        if value & 0x800000:
            value -= 1 << 24
        sttag = int.from_bytes(payload[k + 4 : k + 8], "little")
        samples.append((word >> 24, value, sttag))
    return EsfRaw(payload[:4], samples)


def identity(frame: Frame) -> str:
    if frame.kind == "nmea":
        return frame.data[1:6].decode("ascii", "replace")
    if frame.kind != "ubx":
        return frame.kind
    if frame.data[2:4] == b"\x10\x03":
        return "ESF-RAW"
    try:
        return UBXReader.parse(frame.data).identity
    except Exception:  # an identity pyubx2 does not know
        return f"UBX-{frame.data[2]:02x}-{frame.data[3]:02x}"


def pretty(frame: Frame) -> str:
    head = f"@{frame.offset:>10}  "
    if frame.kind == "ubx" and frame.data[2:4] == b"\x10\x03":
        esf = decode_esf_raw(frame.data)
        parts = []
        for dtype, value, sttag in esf.samples:
            name, unit, scale = ESF_TYPES.get(dtype, (f"type{dtype}", "raw", 1.0))
            parts.append(f"{name}={value * scale:+.4f} {unit} [t={sttag}]")
        return head + f"ESF-RAW reserved0={esf.reserved0.hex()} " + ", ".join(parts)
    if frame.kind == "ubx":
        try:
            return head + str(UBXReader.parse(frame.data))
        except Exception as e:
            return head + f"{identity(frame)} (pyubx2 could not parse: {e}) {frame.data.hex()}"
    if frame.kind == "nmea":
        return head + frame.data.decode("ascii", "replace").rstrip()
    return head + f"{frame.kind} {len(frame.data)} bytes: {frame.data[:32].hex()}"


@dataclass
class Summary:
    size: int = 0
    counts: Counter[str] = field(default_factory=Counter)
    bytes_by_kind: Counter[str] = field(default_factory=Counter)
    texts: Counter[str] = field(default_factory=Counter)
    esf_layouts: Counter[tuple[int, ...]] = field(default_factory=Counter)
    esf_tags_differ: int = 0
    esf_ttags: list[int] = field(default_factory=list)
    esf_reserved0: list[int] = field(default_factory=list)
    esf_accel_norm: list[float] = field(default_factory=list)
    esf_values: dict[int, list[float]] = field(default_factory=dict)

    def add(self, frame: Frame) -> None:
        self.counts[identity(frame)] += 1
        self.bytes_by_kind[frame.kind] += len(frame.data)
        if frame.kind == "nmea" and frame.data[3:6] == b"TXT":
            self.texts[frame.data.decode("ascii", "replace").split(",")[-1].split("*")[0]] += 1
        if frame.kind == "ubx" and frame.data[2:4] == b"\x10\x03":
            esf = decode_esf_raw(frame.data)
            self.esf_layouts[tuple(t for t, _, _ in esf.samples)] += 1
            tags = {s for _, _, s in esf.samples}
            if len(tags) > 1:
                self.esf_tags_differ += 1
            if esf.samples:
                self.esf_ttags.append(esf.samples[0][2])
                self.esf_reserved0.append(int.from_bytes(esf.reserved0, "little"))
            accel = []
            for dtype, value, _ in esf.samples:
                scale = ESF_TYPES.get(dtype, ("", "", 1.0))[2]
                self.esf_values.setdefault(dtype, []).append(value * scale)
                if dtype in (16, 17, 18):
                    accel.append(value * scale)
            if len(accel) == 3:
                self.esf_accel_norm.append(sum(a * a for a in accel) ** 0.5)

    def report(self) -> str:
        out = [f"{self.size} bytes"]
        for kind, n in sorted(self.bytes_by_kind.items()):
            out.append(f"  {kind:<18} {n:>10} bytes ({100 * n / max(self.size, 1):.3f}%)")
        out.append("frames:")
        for ident, n in self.counts.most_common():
            out.append(f"  {ident:<18} {n:>10}")
        if self.texts:
            out.append("NMEA TXT texts:")
            for text, n in self.texts.most_common():
                out.append(f"  {n:>6}  {text}")
        if self.esf_layouts:
            out.append("ESF-RAW data types per message (count):")
            for layout, n in self.esf_layouts.most_common():
                names = [ESF_TYPES.get(t, (f"type{t}",))[0] for t in layout]
                out.append(f"  {n:>8}  {list(layout)} = {names}")
            out.append(f"  messages whose samples carry different sTtags: {self.esf_tags_differ}")
            out.append(self._ttag_report())
            out.append("ESF-RAW values (scaled):")
            for dtype in sorted(self.esf_values):
                v = self.esf_values[dtype]
                name, unit, _ = ESF_TYPES.get(dtype, (f"type{dtype}", "raw", 1.0))
                out.append(
                    f"  {name:<10} n={len(v):<8} mean={statistics.fmean(v):+.4f} "
                    f"sd={statistics.pstdev(v):.4f} min={min(v):+.4f} max={max(v):+.4f} {unit}"
                )
            if self.esf_accel_norm:
                v = self.esf_accel_norm
                q = sorted(v)
                out.append(
                    f"  |accel|    n={len(v):<8} mean={statistics.fmean(v):.4f} "
                    f"p50={q[len(q) // 2]:.4f} sd={statistics.pstdev(v):.4f} m/s^2"
                )
        return "\n".join(out)

    def _ttag_report(self) -> str:
        t = self.esf_ttags
        raw = [b - a for a, b in zip(t, t[1:])]
        if not raw:
            return "  sTtag: fewer than two messages"
        # In the recordings every backward step is 2^24 less a normal step, so sTtag behaves as a
        # 24-bit counter in a U4 field. Only steps that fit that are unwrapped; any other backward
        # step is left negative so that it shows.
        wrap = 1 << 24
        d = [x + wrap if -wrap < x < -wrap + 1_000_000 else x for x in raw]
        wraps = sum(1 for x, y in zip(raw, d) if x != y)
        q = sorted(d)
        median = statistics.median(d)
        # A step well over the usual one means messages are missing from the stream.
        gaps = [x for x in d if x > 1.5 * median]
        missing = sum(round(x / median) - 1 for x in gaps)
        r = self.esf_reserved0
        r_steps = [b - a for a, b in zip(r, r[1:])]

        def pct(p: float) -> int:
            return q[min(len(q) - 1, int(p / 100 * len(q)))]

        lines = [
            f"  sTtag first={t[0]} last={t[-1]} max seen={max(t)}; unwrapped span={sum(d)} ticks "
            f"over {wraps} wraps at 2^24 (tick unit not stated in the documents; see measure.md)",
            f"  sTtag step between messages: n={len(d)} min={q[0]} p1={pct(1)} p50={pct(50)} "
            f"p99={pct(99)} p99.9={pct(99.9)} max={q[-1]}, still non-increasing="
            f"{sum(x <= 0 for x in d)}",
            "  most common steps: "
            + ", ".join(f"{s} ticks x{n}" for s, n in Counter(d).most_common(8)),
            f"  steps over 1.5 x the median ({median:g}): {len(gaps)} "
            f"({100 * len(gaps) / len(d):.2f}% of steps), about {missing} messages missing "
            f"({100 * missing / (len(d) + 1 + missing):.2f}% of those expected)",
            f"  reserved0 as a little-endian U4: first={r[0]} last={r[-1]} span={r[-1] - r[0]}, "
            f"decreasing steps={sum(x < 0 for x in r_steps)}; sTtag span / reserved0 span = "
            f"{sum(d) / (r[-1] - r[0]) if r[-1] != r[0] else float('nan'):.4f}",
        ]
        return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--summary", action="store_true", help="print totals instead of each message")
    ap.add_argument("--only", nargs="+", metavar="IDENTITY", help="e.g. ESF-RAW GNTXT junk")
    ap.add_argument("--limit", type=int, help="stop after printing N messages")
    args = ap.parse_args()

    with open(args.file, "rb") as f:
        buf = f.read()

    if args.summary:
        s = Summary(size=len(buf))
        for frame in frames(buf):
            s.add(frame)
        print(s.report())
        return 0

    printed = 0
    try:
        for frame in frames(buf):
            if args.only and identity(frame) not in args.only:
                continue
            print(pretty(frame))
            printed += 1
            if args.limit and printed >= args.limit:
                break
    except BrokenPipeError:  # piped into `head`
        sys.stderr.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

</details>

**What came out.** Every byte of every log is accounted for:

| log            |      bytes | `ESF-RAW` | `GNTXT` | bad-checksum frames | stray bytes |
| -------------- | ---------: | --------: | ------: | ------------------: | ----------: |
| `LOG00001.TXT` |    179 473 |     2 628 |      22 |                   0 |          21 |
| `LOG00002.TXT` | 39 260 528 |   574 394 |   5 933 |                   0 |          14 |
| `LOG00003.TXT` | 17 748 762 |   259 676 |   2 670 |                   0 |          14 |
| `LOG00004.TXT` |  4 773 308 |    69 839 |     713 |                   0 |          14 |

- **The stray bytes** in each log are its last frame, cut off: the file ends partway through an
  `ESF-RAW` that starts `b5 62 10 03 3c 00`.
- **Every `GNTXT` sentence** reads `$GNTXT,01,01,00,txbuf alloc S*12`. Neither document explains
  that text.
- **No other message** is in any log.

*Framing.* All 906 537 `ESF-RAW` messages have the same seven samples, in the same order:

| `dataType` | meaning (`[IM]` Table 15) | scale        |
| ---------: | ------------------------- | ------------ |
|         16 | x-axis accelerometer      | m/s² · 2⁻¹⁰  |
|         17 | y-axis accelerometer      | m/s² · 2⁻¹⁰  |
|         18 | z-axis accelerometer      | m/s² · 2⁻¹⁰  |
|         14 | x-axis gyroscope          | deg/s · 2⁻¹² |
|         13 | y-axis gyroscope          | deg/s · 2⁻¹² |
|          5 | z-axis gyroscope          | deg/s · 2⁻¹² |
|         12 | gyroscope temperature     | °C · 10⁻²    |

In every message all seven samples carry the same `sTtag`.

*The step in `sTtag` from one message to the next*, in ticks:

| log            | steps   | min |  p1 | p50 | p99 | p99.9 |   max | steps over 1.5 × p50 | messages missing, about |
| -------------- | ------- | --: | --: | --: | --: | ----: | ----: | -------------------: | ----------------------: |
| `LOG00001.TXT` | 2 627   | 156 | 228 | 257 | 514 | 1 546 | 1 801 |          49 (1.87 %) |             71 (2.63 %) |
| `LOG00002.TXT` | 574 393 | 156 | 228 | 257 | 515 | 1 543 | 2 059 |      13 994 (2.44 %) |         22 087 (3.70 %) |
| `LOG00003.TXT` | 259 675 | 158 | 228 | 257 | 515 | 1 520 | 2 059 |       6 387 (2.46 %) |          9 125 (3.39 %) |
| `LOG00004.TXT` | 69 838  | 156 | 228 | 257 | 515 | 1 513 | 1 802 |       1 681 (2.41 %) |          2 353 (3.26 %) |

- **The usual step is 255 to 259 ticks.** 257 is the most common in every log.
- **Steps near 514, 771 and so on are whole multiples of it.** With no frame corrupt, these are
  messages missing from the stream.
- **The "messages missing" column** rounds each long step to a multiple of the median and counts
  the multiples beyond one.

*`sTtag` wraps.* It runs backwards 9, 4 and 1 times in `LOG00002`, `LOG00003` and `LOG00004`, and
never in `LOG00001`. Each time, the backward step is 2²⁴ less a normal step. So although the field
is typed U4, it behaves as a 24-bit counter. The largest value seen is 16 776 997, just under
2²⁴ = 16 777 216. The script unwraps these steps before computing the statistics above.

*`reserved0` counts too.* Read as a little-endian U4, it never decreases in any log. Over each log,
the unwrapped `sTtag` span divided by the `reserved0` span is 25.7259, 25.7205, 25.7194 and 25.7222.
So the message carries two counters with a steady ratio of about 25.72. The ratio comes out that
steady only once the wraps are unwrapped, which confirms them.

*Two regularities I can't explain.*
- All four logs start at `sTtag` 6 518 to 6 527, and `reserved0` 2 745 to 2 819.
- `LOG00002`, `LOG00003` and `LOG00004` all end with `sTtag` between 1 710 103 and 1 710 362, after
  different numbers of wraps.

*The values* (means over each log; the spread is in each summary):

| log            | \|accel\| (m/s²) | `gyro_x` (deg/s) | `gyro_y` (deg/s) | `gyro_z` (deg/s) | gyro temp (°C) |
| -------------- | ---------------: | ---------------: | ---------------: | ---------------: | -------------: |
| `LOG00001.TXT` |          10.4359 |          −0.0364 |          −0.4909 |          −0.0766 | 22.95 to 25.07 |
| `LOG00002.TXT` |          10.4679 |          −0.0605 |          −0.4320 |          +0.0172 | 21.34 to 33.05 |
| `LOG00003.TXT` |          10.5203 |          −0.0791 |          −0.4315 |          +0.0245 | 21.00 to 34.89 |
| `LOG00004.TXT` |          10.4820 |          −0.0664 |          −0.4481 |          +0.0156 | 20.86 to 31.89 |

*Where the raw data is.* Nowhere any more. The logs were copied off the SD card for this lab and the
copies deleted afterwards. The four `--summary` outputs below, from `tools/ubx-dump.py` as
committed, are the record. Every number in this section comes from them.

<details>
<summary>The four summaries, verbatim</summary>

`pixi run python tools/ubx-dump.py LOG00001.TXT --summary`:

```text
179473 bytes
  junk                       21 bytes (0.012%)
  nmea                      748 bytes (0.417%)
  ubx                    178704 bytes (99.572%)
frames:
  ESF-RAW                  2628
  GNTXT                      22
  junk                        1
NMEA TXT texts:
      22  txbuf alloc S
ESF-RAW data types per message (count):
      2628  [16, 17, 18, 14, 13, 5, 12] = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z', 'gyro_temp']
  messages whose samples carry different sTtags: 0
  sTtag first=6527 last=697112 max seen=697112; unwrapped span=690585 ticks over 0 wraps at 2^24 (tick unit not stated in the documents; see measure.md)
  sTtag step between messages: n=2627 min=156 p1=228 p50=257 p99=514 p99.9=1546 max=1801, still non-increasing=0
  most common steps: 257 ticks x1126, 258 ticks x558, 256 ticks x244, 259 ticks x151, 255 ticks x63, 228 ticks x45, 260 ticks x25, 254 ticks x20
  steps over 1.5 x the median (257): 49 (1.87% of steps), about 71 messages missing (2.63% of those expected)
  reserved0 as a little-endian U4: first=2799 last=29643 span=26844, decreasing steps=0; sTtag span / reserved0 span = 25.7259
ESF-RAW values (scaled):
  gyro_z     n=2628     mean=-0.0766 sd=0.6448 min=-10.2212 max=+0.4114 deg/s
  gyro_temp  n=2628     mean=+24.1357 sd=0.5741 min=+22.9500 max=+25.0700 degC
  gyro_y     n=2628     mean=-0.4909 sd=0.1773 min=-8.1709 max=+0.6934 deg/s
  gyro_x     n=2628     mean=-0.0364 sd=0.1313 min=-4.2380 max=+1.3870 deg/s
  accel_x    n=2628     mean=-0.3826 sd=0.0198 min=-0.5264 max=-0.0156 m/s^2
  accel_y    n=2628     mean=-0.0960 sd=0.0248 min=-0.6455 max=+0.2637 m/s^2
  accel_z    n=2628     mean=+10.4284 sd=0.0142 min=+10.3037 max=+10.6016 m/s^2
  |accel|    n=2628     mean=10.4359 p50=10.4357 sd=0.0142 m/s^2
```

`pixi run python tools/ubx-dump.py LOG00002.TXT --summary`:

```text
39260528 bytes
  junk                       14 bytes (0.000%)
  nmea                   201722 bytes (0.514%)
  ubx                  39058792 bytes (99.486%)
frames:
  ESF-RAW                574394
  GNTXT                    5933
  junk                        1
NMEA TXT texts:
    5933  txbuf alloc S
ESF-RAW data types per message (count):
    574394  [16, 17, 18, 14, 13, 5, 12] = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z', 'gyro_temp']
  messages whose samples carry different sTtags: 0
  sTtag first=6522 last=1710362 max seen=16776997; unwrapped span=152698784 ticks over 9 wraps at 2^24 (tick unit not stated in the documents; see measure.md)
  sTtag step between messages: n=574393 min=156 p1=228 p50=257 p99=515 p99.9=1543 max=2059, still non-increasing=0
  most common steps: 257 ticks x317070, 258 ticks x122507, 256 ticks x51930, 259 ticks x22551, 255 ticks x8364, 514 ticks x4919, 228 ticks x4683, 235 ticks x4581
  steps over 1.5 x the median (257): 13994 (2.44% of steps), about 22087 messages missing (3.70% of those expected)
  reserved0 as a little-endian U4: first=2819 last=5939670 span=5936851, decreasing steps=0; sTtag span / reserved0 span = 25.7205
ESF-RAW values (scaled):
  gyro_z     n=574394   mean=+0.0172 sd=0.1989 min=-55.6560 max=+17.7974 deg/s
  gyro_temp  n=574394   mean=+31.3212 sd=1.4250 min=+21.3400 max=+33.0500 degC
  gyro_y     n=574394   mean=-0.4320 sd=0.3847 min=-66.9136 max=+76.3723 deg/s
  gyro_x     n=574394   mean=-0.0605 sd=0.2283 min=-53.1865 max=+41.2654 deg/s
  accel_x    n=574394   mean=-0.3175 sd=0.0284 min=-4.2959 max=+7.0410 m/s^2
  accel_y    n=574394   mean=-0.1780 sd=0.0240 min=-2.6660 max=+2.8154 m/s^2
  accel_z    n=574394   mean=+10.4615 sd=0.0260 min=+5.6084 max=+16.2949 m/s^2
  |accel|    n=574394   mean=10.4679 p50=10.4691 sd=0.0263 m/s^2
```

`pixi run python tools/ubx-dump.py LOG00003.TXT --summary`:

```text
17748762 bytes
  junk                       14 bytes (0.000%)
  nmea                    90780 bytes (0.511%)
  ubx                  17657968 bytes (99.488%)
frames:
  ESF-RAW                259676
  GNTXT                    2670
  junk                        1
NMEA TXT texts:
    2670  txbuf alloc S
ESF-RAW data types per message (count):
    259676  [16, 17, 18, 14, 13, 5, 12] = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z', 'gyro_temp']
  messages whose samples carry different sTtags: 0
  sTtag first=6518 last=1710361 max seen=16776991; unwrapped span=68812707 ticks over 4 wraps at 2^24 (tick unit not stated in the documents; see measure.md)
  sTtag step between messages: n=259675 min=158 p1=228 p50=257 p99=515 p99.9=1520 max=2059, still non-increasing=0
  most common steps: 257 ticks x142623, 258 ticks x53997, 256 ticks x24579, 259 ticks x10673, 255 ticks x4202, 514 ticks x2517, 228 ticks x2081, 235 ticks x2061
  steps over 1.5 x the median (257): 6387 (2.46% of steps), about 9125 messages missing (3.39% of those expected)
  reserved0 as a little-endian U4: first=2798 last=2678314 span=2675516, decreasing steps=0; sTtag span / reserved0 span = 25.7194
ESF-RAW values (scaled):
  gyro_z     n=259676   mean=+0.0245 sd=0.0417 min=-0.3735 max=+0.2515 deg/s
  gyro_temp  n=259676   mean=+32.9811 sd=2.5213 min=+21.0000 max=+34.8900 degC
  gyro_y     n=259676   mean=-0.4315 sd=0.0462 min=-2.1343 max=+0.3809 deg/s
  gyro_x     n=259676   mean=-0.0791 sd=0.0511 min=-1.1433 max=+0.6782 deg/s
  accel_x    n=259676   mean=-0.2899 sd=0.0245 min=-0.4932 max=+0.0703 m/s^2
  accel_y    n=259676   mean=-1.1801 sd=0.0263 min=-1.3193 max=-0.9189 m/s^2
  accel_z    n=259676   mean=+10.4498 sd=0.0184 min=+10.2314 max=+10.8105 m/s^2
  |accel|    n=259676   mean=10.5203 p50=10.5232 sd=0.0203 m/s^2
```

`pixi run python tools/ubx-dump.py LOG00004.TXT --summary`:

```text
4773308 bytes
  junk                       14 bytes (0.000%)
  nmea                    24242 bytes (0.508%)
  ubx                   4749052 bytes (99.492%)
frames:
  ESF-RAW                 69839
  GNTXT                     713
  junk                        1
NMEA TXT texts:
     713  txbuf alloc S
ESF-RAW data types per message (count):
     69839  [16, 17, 18, 14, 13, 5, 12] = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z', 'gyro_temp']
  messages whose samples carry different sTtags: 0
  sTtag first=6525 last=1710103 max seen=16776992; unwrapped span=18480794 ticks over 1 wraps at 2^24 (tick unit not stated in the documents; see measure.md)
  sTtag step between messages: n=69838 min=156 p1=228 p50=257 p99=515 p99.9=1513 max=1802, still non-increasing=0
  most common steps: 257 ticks x37889, 258 ticks x15715, 256 ticks x6303, 259 ticks x2790, 255 ticks x927, 514 ticks x618, 228 ticks x576, 235 ticks x553
  steps over 1.5 x the median (257): 1681 (2.41% of steps), about 2353 messages missing (3.26% of those expected)
  reserved0 as a little-endian U4: first=2745 last=721221 span=718476, decreasing steps=0; sTtag span / reserved0 span = 25.7222
ESF-RAW values (scaled):
  gyro_z     n=69839    mean=+0.0156 sd=0.0418 min=-0.1907 max=+0.2209 deg/s
  gyro_temp  n=69839    mean=+29.2351 sd=2.4833 min=+20.8600 max=+31.8900 degC
  gyro_y     n=69839    mean=-0.4481 sd=0.0688 min=-1.4331 max=+0.5259 deg/s
  gyro_x     n=69839    mean=-0.0664 sd=0.0498 min=-0.3203 max=+0.1980 deg/s
  accel_x    n=69839    mean=-0.2850 sd=0.0341 min=-0.4893 max=-0.0742 m/s^2
  accel_y    n=69839    mean=-0.2055 sd=0.0186 min=-0.3633 max=-0.0420 m/s^2
  accel_z    n=69839    mean=+10.4761 sd=0.0217 min=+10.2451 max=+10.7500 m/s^2
  |accel|    n=69839    mean=10.4820 p50=10.4849 sd=0.0223 m/s^2
```

</details>

**What I learned.**
- **Each `ESF-RAW` message is one complete IMU sample.** Three accelerometer axes, three gyro axes
  and the gyro temperature share one `sTtag`. So M2's driver can turn each message into one
  `sensor_msgs/Imu`, without matching samples across messages. That is what `[IM §3.2.7.6]`
  promises: "one sample of every data type per message".
- **`sTtag` is a 24-bit counter in a 32-bit field.** Anything that maps it to GNSS time has to
  unwrap it, and it wraps every 2²⁴ ticks. How long that is in seconds is still unknown.
- **The rate in Hz is not known yet.** The logs carry no clock of their own, and neither document
  gives the unit of `ESF-RAW.sTtag`. The 1 ms resolution in `[IM §3.2.5.2]` is stated for
  `ESF-MEAS`, not `ESF-RAW`. The way to close it is one capture with host timestamps. The
  unwrapped `sTtag` span over the wall-clock span gives the tick, and from it the rate. Counting
  messages per second would come out low, by however many messages are dropped.
- **About 3 % of the messages never reached the card, with no frame corrupt.** So whatever records
  `ESF-RAW` has to expect gaps and find them from `sTtag`, not assume a fixed rate. The
  `txbuf alloc S` warnings look related, but they don't line up with the gaps, so I can't yet say
  what they mean.
- **Raw means raw.** The magnitude of the acceleration, averaged over each log, is 10.44 to
  10.52 m/s², where gravity alone would give about 9.8. The gyro's y-axis sits at about −0.43 to
  −0.49 deg/s. Neither is corrected in `ESF-RAW`. Both are what calibration (M6) and the Allan
  variance (M2) will have to account for.
- **Decode with every byte accounted for.** A parser that silently skips what it can't read would
  have hidden the dropped messages and the truncated last frame.

> [!TODO]
> Correct the "What I learned" sections in your own words: what surprised you, and what you would
> do differently. Do you know who flashed HPS 1.40?

## What to try next

- **The IMU rate (#11).** Capture `ESF-RAW` with host timestamps and divide the unwrapped `sTtag`
  span by the wall-clock span. UART1 can be read from a USB-serial adapter on `TX1`, listening
  alongside the OpenLog without changing anything. Putting `ESF-RAW` on USB instead would take a
  `VALSET`, in RAM only.
- **The stored configuration (#9).** `VALGET` each layer (RAM, BBR, flash, default) for the port,
  protocol and message-rate keys, and record what the board holds before the box changes it.
- **The IOREF switch, before the Pi is wired.** The photo shows the switch but not reliably which
  way it is set. On the Budget board, IOREF sets the UART voltage level. Confirm this board's
  setting gives 3.3 V on the pins the Pi will use, with the AD3, before connecting a GPIO.
- **The dropped messages (#33).** Record `UBX-MON-COMMS` alongside `ESF-RAW` and see whether the
  drops follow the transmit buffer.

## What it closes

- [#1](../../reference/open-questions/index.md#blocking-m1): **MEASURED**, HPS 1.40, protocol
  33.40.
- Opens [#32](../../reference/open-questions/index.md#blocking-m1): every key the box sets has yet
  to be checked against the HPS 1.40 interface description, which is not yet in the ledger's
  sources.
- [#11](../../reference/open-questions/index.md#blocking-m2) stays **OPEN**. The framing is
  answered: one sample of each of the seven types per message, with one shared `sTtag`, and a usual
  step of 257 ticks. The rate in Hz waits for a host-clocked capture.
- [#2](../../reference/open-questions/index.md#blocking-m1) stays **OPEN**, but the silkscreen
  answers its first step. `TPS` and `EVT` are on J4, the PIXHAWK + POWER connector, and `TPS` and
  `EXTINT` are on the bottom header. Probing the pin with the AD3 is still to come.
- [#14](../../reference/open-questions/index.md#blocking-m2) stays **OPEN**. On this board, UART1
  is on both J4 and the bottom header, and a switch connects the XBee socket to UART1 or UART2. As
  found, the OpenLog was on UART1 and the switch gave the empty XBee socket UART2.
- [#10](../../reference/open-questions/index.md#blocking-m2) and
  [#13](../../reference/open-questions/index.md#blocking-m2) stay **OPEN**, with one new fact for
  both: `sTtag` wraps at 2²⁴.
- Opens [#33](../../reference/open-questions/index.md#blocking-m2): why about 3 % of `ESF-RAW`
  messages are missing from the UART recordings, and what `txbuf alloc S` means.
