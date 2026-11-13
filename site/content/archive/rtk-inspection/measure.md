---
summary: The ZED-F9R on the ArduSimple board runs firmware HPS 1.40, protocol version 33.40, read from `UBX-MON-VER` over USB.
---

## What I set out to check

- [#1](../../reference/open-questions/index.md#blocking-m1): which firmware the F9R runs. Every
  configuration key the box will set, and which UBX messages exist, depend on it, so M1's config
  tool cannot be written against the right interface description until this is known.
- [#11](../../reference/open-questions/index.md): the IMU sample rate and how `ESF-RAW` frames it.

> [!TODO]
> #11 has no reading yet. Either measure it from the UART that already carries UBX (read-only), or
> narrow this probe to #1 and rewrite the entry's paragraph to match.

## What I did

**First, u-center 2 on Windows.** I polled `UBX-MON-VER` there, and used its answer to check the
reading below.

> [!TODO]
> u-center 2's version and the Windows version it ran on.

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

The board came up as `/dev/ttyACM0` (`pixi run get-firmware /dev/ttyACM0`). The kernel log from
when it was plugged in shows the F9R's own USB, handled by the generic CDC-ACM driver, with no
USB-serial bridge chip in between:

```text
usb 1-1.1.3: New USB device found, idVendor=1546, idProduct=01a9, bcdDevice= 1.00
cdc_acm 1-1.1.3:1.0: ttyACM0: USB ACM device
```

udev reports the interfaces as `:020201:0a00ff:`: a communications interface with class 02, subclass
02 (ACM) and protocol 01, and a CDC data interface with class 0a. Its stable name is
`/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_GNSS_receiver-if00`. The node is owned by
group `uucp`, so the user running the script needs to be in that group.

> [!TODO]
> Which connector on the board the cable went to, and how many times the script was run.

**Along the way, picocom.** Opening the same port in picocom showed NMEA sentences flowing on USB
and no visible UBX. That is the board's stored configuration rather than a fault: I had earlier
configured UBX output on the board's UART pins, not on USB.

## Results

> [!TODO]
> Paste the script's output verbatim, the hex line and the parsed line. The reading reported so far
> was `extension_04='MOD-ZED-F9R'`, but the receiver writes `MOD=` like `FWVER=` and `PROTVER=`, so
> it may have been retyped.

| field          | value                    |
| -------------- | ------------------------ |
| `swVersion`    | `EXT CORE 1.00 (f8b901)` |
| `hwVersion`    | `00190000`               |
| extension 1    | `ROM BASE 0x118B2060`    |
| extension 2    | `FWVER=HPS 1.40`         |
| extension 3    | `PROTVER=33.40`          |
| extension 4    | `MOD-ZED-F9R` (as typed) |
| extension 5    | `GPS;GLO;GAL;BDS`        |
| extension 6    | `SBAS;QZSS`              |

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
- **The board is not at factory settings.** My earlier configuration survived power cycles, so it
  sits in BBR or flash. Before the box changes anything, the stored layers should be read back and
  recorded, so that what the board was set to before the box is known.

> [!TODO]
> Correct this in your own words: what surprised you, and what you would do differently.

## What it closes

- [#1](../../reference/open-questions/index.md#blocking-m1): **MEASURED**, HPS 1.40.
- Opens: the configuration keys have not been checked against the HPS 1.40 interface description.
  Added to the ledger as a new question.
