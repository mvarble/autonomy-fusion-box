---
summary: The ZED-F9R on the ArduSimple board runs firmware HPS 1.40, protocol version 33.40, read from `UBX-MON-VER` over USB.
---

<script>
	import board from './board.jpg';
</script>

## What I set out to check

- [#1](../../reference/open-questions/index.md#blocking-m1): which firmware the F9R runs. Every
  configuration key the box will set, and which UBX messages exist, depend on it, so M1's config
  tool cannot be written against the right interface description until this is known.
- [#11](../../reference/open-questions/index.md): the IMU sample rate and how `ESF-RAW` frames it.

> [!TODO]
> #11 has no reading yet. Either measure it from the UART that already carries UBX (read-only), or
> narrow this probe to #1 and rewrite the entry's paragraph to match.

## What I did

**The board.** This is the ArduSimple board in its 3D-printed enclosure, powered over USB. The
coloured wires are serial connections I set up in u-center 2 a long time ago, when I was trying to
get GPS, IMU and INS estimates out of the board. They were still in place for this probe.

<figure>
	<img src={board} alt="The ArduSimple board in a black enclosure, with a red, a blue, a yellow and a green wire soldered or plugged into its headers and leaving through the enclosure wall. The u-blox ZED-F9R module sits at the lower right, beside the SMA antenna connector." width="1444" height="1362" />
	<figcaption>The board as probed. The F9R module is at the lower right, next to the SMA antenna connector and the POWER + GPS USB-C port.</figcaption>
</figure>

What the photo shows, read from the silkscreen:

- **The module** is marked `ZED-F9R-01B-00`.
- **Two USB-C ports.** The one labelled POWER + XBEE is at the upper left and POWER + GPS at the
  right. The probe used POWER + GPS.
- **The wires.** Yellow and green go to the bottom header. Green is in the pin labelled `RX1`.
  Yellow is in the pin beside it, whose label the wire hides. Red goes to the top header, at the pin
  above `LED7` (`5V IN/OUT`). Blue goes to the end of the XBee socket's lower row, next to a `GND`
  label. All four leave through the enclosure wall.
- **J4, a 6-pin JST connector labelled PIXHAWK + POWER**, at the right edge. Its pins read, from 1
  to 6: `VIN`, `RX1`, `TX1`, `TPS`, `EVT`, `GND`. So UART1, the timepulse and an event input are on
  one connector.
- **The bottom header** also carries `RX2`, `TX2`, `GEOFENCE`, `EXTINT`, `TPS`, `GND`, `RST`,
  `SDA` and `SCL`. There is a separate `TPS` pad labelled `J9` near the top.
- **A slide switch labelled XBEE TO GPS UART1 / XBEE TO GPS UART2** picks which of the F9R's UARTs
  the XBee socket reaches. Its position cannot be read reliably from the photo.
- **A second slide switch** chooses between `IOREF = 3V3, 5V = OUTPUT` and
  `IOREF & 5V ARE INPUTS`.
- **The footprint labelled `BAT`** in the middle of the board, a circle with two pads, has nothing
  fitted.
- **LEDs:** `POWER` is lit, and so is `NO RTK`, in red. `PVT` is dark, and the photo was taken
  indoors. `5V IN/OUT`, `IOREF` and one of the `GPS>XBEE` / `XBEE>GPS` pair are lit as well.

> [!TODO]
> Confirm the wires: is yellow on `TX1`, red on 5 V and blue on ground? And what is on the other end
> of them, a USB-serial adapter or something else? Which switch position is the XBee switch in?

**First, u-center 2 on Windows.** I polled `UBX-MON-VER` there, and used its answer to check the
reading below.

**Then the same poll from Linux, with pyubx2.** The board's USB port enumerates as a serial device,
and `UBX-MON-VER` is a read-only poll: an 8-byte request with no payload, which changes no
configuration. The script sends the poll and prints the first `MON-VER` reply, both as raw hex and
parsed:

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

It runs from the Pixi environment at the repository root (`pixi run get-firmware <path>`): Python
3.15.2, pyubx2 1.4.1 and pyserial 3.5, on Arch Linux, kernel 7.2.14-arch1-1. `protfilter=2` makes
the reader skip the NMEA sentences that stream on the same port, so the reply is not lost among
them.

The board has two USB-C connectors. The cable went to the one labelled **POWER + GPS**, next to the
antenna connector. The board came up as `/dev/ttyACM0` (`pixi run get-firmware /dev/ttyACM0`). The
kernel log from when it was plugged in shows that this connector is the F9R's own USB, handled by
the generic CDC-ACM driver, with no USB-serial bridge chip in between:

```text
usb 1-1.1.3: New USB device found, idVendor=1546, idProduct=01a9, bcdDevice= 1.00
cdc_acm 1-1.1.3:1.0: ttyACM0: USB ACM device
```

udev reports the interfaces as `:020201:0a00ff:`: a communications interface with class 02, subclass
02 (ACM) and protocol 01, and a CDC data interface with class 0a. Its stable name is
`/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_GNSS_receiver-if00`. The node is owned by
group `uucp`, so the user running the script needs to be in that group.

> [!TODO]
> How many times the script was run.

**Along the way, picocom.** Opening the same port in picocom showed NMEA sentences flowing on USB
and no visible UBX. That is the board's stored configuration rather than a fault: I had earlier
configured UBX output on the board's UART pins, not on USB.

## Results

The reply, exactly as the script printed it (228 bytes):

```text
b5620a04dc0045585420434f524520312e3030202866386239303129000000000000000030303139303030300000524f4d20424153452030783131384232303630000000000000000000000046575645523d48505320312e34300000000000000000000000000000000050524f545645523d33332e343000000000000000000000000000000000004d4f443d5a45442d463952000000000000000000000000000000000000004750533b474c4f3b47414c3b424453000000000000000000000000000000534241533b515a535300000000000000000000000000000000000000000006f1
```

I checked the frame by hand as well as through pyubx2:

- `b5 62` is the sync, and `0a 04` is the class and ID of `MON-VER`.
- `dc 00` is the payload length, little-endian: 220 bytes. That matches the bytes received, and
  fits the layout of a 30-byte `swVersion`, a 10-byte `hwVersion`, then six 30-byte extensions
  (30 + 10 + 6 × 30 = 220).
- The checksum, the 8-bit Fletcher sum over class, ID, length and payload, comes out to `06 f1`, the
  last two bytes received.

Each field is NUL-padded ASCII:

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

## What I learned

- **The firmware is HPS 1.40, protocol 33.40.** The ledger's interface description `[ID]` is the
  HPS 1.30 one, so every key the box sets has to be checked against the HPS 1.40 interface
  description instead. HPS 1.40 does meet the "HPS 1.30 or later" condition for UBX output on
  UART2 `[IM §3.1.3]`.
- **A receiver's version is one poll away, and needs no vendor tool.** The same 8 bytes work from
  any host, which is what M1's config tool will do on every start.
- **USB and the UART pins are configured separately.** Each port has its own output protocols and
  its own per-message rates, which is why USB showed only NMEA while the UART carries UBX.
- **The board is not at factory settings.** UBX still comes out of the UART pins from the
  configuration I made long ago. Settings in RAM are lost when power goes. BBR keeps them only
  while a backup supply holds, and the `BAT` footprint has nothing fitted. So the configuration is
  most likely in flash. #9 asks exactly this, and reading the layers back with `VALGET` would
  answer it. Before the box changes anything, those stored layers should be read back and recorded,
  so that what the board was set to before the box is known.

> [!TODO]
> Correct this in your own words: what surprised you, and what you would do differently.

## What it closes

- [#1](../../reference/open-questions/index.md#blocking-m1): **MEASURED**, HPS 1.40, protocol
  33.40.
- Opens [#32](../../reference/open-questions/index.md#blocking-m1): every key the box sets has yet to
  be checked against the HPS 1.40 interface description, which is not yet in the ledger's sources.
- [#2](../../reference/open-questions/index.md#blocking-m1) stays **OPEN**, but the silkscreen
  answers its first step. `TPS` and `EVT` are on J4, the PIXHAWK + POWER connector, and `TPS` and
  `EXTINT` are on the bottom header. Probing the pin with the AD3 is still to come.
- [#14](../../reference/open-questions/index.md#blocking-m2) stays **OPEN**. On this board, UART1
  is on both J4 and the bottom header, and a switch connects the XBee socket to UART1 or UART2.
