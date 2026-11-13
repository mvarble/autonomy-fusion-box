---
summary: A hands-on warm-up with the ArduSimple ZED-F9R board before working through the ledger's open questions. It finds the documentation, configures UART1 to send the IMU's raw samples, checks the bytes through an FTDI adapter, then records and parses them, first through the adapter and then with an SD-card logger.
---

<script>
	import board from './board.jpg';
	import rails from './ardusimple-arduino-rails.jpg';
	import esfRaw from './id-esf-raw.png';
	import ucenter from './ucenter-uart1-recording.png';
	import picocom from './ftdi-picocom.png';
	import ioref from './ioref-switch.jpg';
	import step4 from './step4-record-parse.png';
	import openlogConfig from './openlog-config.png';
</script>

I trained as a mathematician and work as a navigation engineer.
Embedded development sits right next to that work, but nothing in my studies touched it.
This box is how I am learning the hardware side, with an AI assistant alongside.
The [ledger](../../reference/open-questions/index.md) is full of questions about this receiver that the assistant raised, and answering them will mean polling messages, reading bytes and wiring pins.
Before that, I wanted a feel for the basics with my own hands: get data out of the board, into a file, and parsed.

This lab does that in five steps, each building on the last:

1. [find the documentation](#1-finding-the-documentation);
2. [configure UART1 in u-center 2](#2-configuring-uart1-in-u-center-2) to send the messages I care about;
3. [check that bytes flow](#3-checking-that-bytes-flow), through an FTDI USB-serial adapter;
4. [record the bytes to a file and parse it](#4-recording-a-file-and-parsing-it);
5. [swap in an SD-card logger and parse its file](#5-recording-with-the-openlog).

Each step says what it is for, how it is done, what to look for, and what it taught.
It answers no ledger question by itself.
[What comes next](#what-comes-next) lists the ones it prepares for.

## The setup

<figure>
	<img src={board} alt="The ArduSimple board in an open black 3D-printed enclosure on a bench mat, wire strippers beside it. Yellow, green, blue and red wires run from the board's headers out through a rough hole melted in the enclosure wall, their stripped ends loose. The u-blox ZED-F9R module sits at the lower right, beside the gold SMA antenna connector." width="1200" height="1600" />
	<figcaption>The board in its enclosure, with the UART1 and power wires leaving through a hole in the wall. The F9R module is at the lower right, next to the SMA antenna connector.</figcaption>
</figure>

The board is ArduSimple's simpleRTK2B Fusion, which carries a u-blox ZED-F9R: a GNSS receiver with an IMU inside.
It sits in a 3D-printed enclosure and is powered over USB.
The enclosure is a design I found online, [on Thingiverse](https://www.thingiverse.com/thing:3551604), and the Santa Barbara Public Library printed it for me, for free.
A public library is worth asking before buying a printer for one part.
The design has no opening for wires, so to close the lid and still reach UART1 I melted a hole through the wall with my soldering iron.
Neither the enclosure nor the iron was made for this, but the wires fit.

Besides the board, the lab uses:

- **u-center 2**, u-blox's configuration tool, on Windows;
- **an FTDI USB-serial adapter**, and **picocom**, a minimal serial terminal, on Linux;
- **a SparkFun OpenLog**, a small board that writes whatever arrives on its serial input to an SD card;
- **my desktop computer**, running Arch Linux (kernel 7.2.14-arch1-1), with Python 3.15.2, pyubx2 1.4.1 and pyserial 3.5 from the Pixi environment at the repository root.

## 1. Finding the documentation

**What it is for.** Knowing which pin is which, which tool configures the receiver, and where its messages are defined.
Everything after this step leans on it.

**How it is done.** Start at the product and follow the links down to the chip's maker:

- **The [product page](https://www.ardusimple.com/product/simplertk2b-fusion/)** leads to the board's [hookup guide](https://www.ardusimple.com/rtk-ins-simplertk2b-f9r-hookup-guide/).
- **The pin details** were not in the hookup guide.
  They were in the [guide for a sibling board](https://www.ardusimple.com/user-guide-simplertk2b-budget/), the simpleRTK2B Budget, which carries a ZED-F9P rather than the F9R.
  Its section on the [Arduino rails](https://www.ardusimple.com/user-guide-simplertk2b-budget/#arduino) shows which header pins carry which UART.
  That guide also points to u-center 2.
- **u-blox's own documents** start from the [getting-started note for the ZED-F9R](https://content.u-blox.com/sites/default/files/documents/ZED-F9R-GettingStarted_AppNote_UBX-22035176.pdf), linked at the bottom of the hookup guide.
  From there:
  - the [integration manual](https://www.u-blox.com/docs/UBX-20039643) explains how the receiver behaves;
  - the [interface description](https://www.u-blox.com/docs/UBX-22010984) defines every message and configuration key.

**What to look for.** On the Arduino rails, the pins a UART needs:

<figure>
	<img src={rails} alt="ArduSimple's user guide for the simpleRTK2B Budget, section Arduino rails: a photo of the board with the header pins highlighted, and a list. GND should always be connected. 5V_IN can power the board, with the 5V switch set to input. IOREF is an input that sets the voltage level of the next pins, from 1.2 V to 5.5 V. TX1 and RX1 are ZED-F9P UART1 TX and RX. TX2 and RX2 are the XBee UART, also connected to the ZED-F9P's UART2. Connecting your own hardware to UART1 or UART2 makes it mandatory to connect IOREF to the voltage your hardware needs." width="826" height="1011" />
	<figcaption>The Arduino rails, from ArduSimple's guide to the simpleRTK2B Budget, a sibling board with a ZED-F9P. Screenshot of <a href="https://www.ardusimple.com/user-guide-simplertk2b-budget/#arduino">the guide</a>.</figcaption>
</figure>

- `TX1` is the receiver's UART1 output, which is the pin to listen on.
- `GND` must always be shared with whatever is connected.
- `IOREF` sets the voltage the UART pins run at, and has to match the hardware on the other end.

The interface description shows how much of the receiver lives in UBX messages.
Each has a class, an ID and a fixed layout, like `ESF-RAW`, which carries the IMU's raw samples:

<figure>
	<img src={esfRaw} alt="u-blox interface description section 3.11.4, UBX-ESF-RAW (0x10 0x03), raw sensor measurements. Output message, length 4 + n times 8 bytes. Payload: a 4-byte reserved0 field, then a repeated group of a 4-byte data field, whose bits 23 to 0 are dataField and bits 31 to 24 dataType, and a 4-byte sTtag, the sensor time tag." width="862" height="490" />
	<figcaption>Interface description §3.11.4, <code>UBX-ESF-RAW</code>. Screenshot of <a href="https://www.u-blox.com/docs/UBX-22010984">the interface description</a>.</figcaption>
</figure>

**What I learned.**
- **The documents come in layers.** The board maker documents the board, and the chip maker documents the chip.
  The pins are the board's business, and the messages are the chip's.
- **A sibling board's guide is a start, not an answer.** This board's own silkscreen has the final word on which pin is which.
- **The messages are not fixed.** What comes out of the chip, and so out of UART1, is whatever it has been configured to send.
  Out of the box that is a set of NMEA text sentences; choosing the messages is my job, and step 2 does it.
- **Every message has a definition to read before parsing it.** `ESF-RAW`'s layout is the one this lab ends up decoding.

## 2. Configuring UART1 in u-center 2

**What it is for.** Making the receiver send the messages I care about on UART1, the port on the header pins, so the rest of the lab has something to look at.
At this point I didn't know what UART1's settings were, or even what a baud rate was.
Rather than learn the protocol first, I reached for u-center 2, u-blox's graphical tool.
It connects to the receiver, shows the messages it is sending, and lists every configuration key with its current value, so it does much of the discovery for you.

What it shows is that, out of the box, UART1 runs at 38400 baud and sends NMEA text.
UBX is enabled on it, but no UBX message is switched on (integration manual §3.1.3; USB starts the same way).

**How it is done.** In u-center 2, connect to the receiver.
Then, under *Device configuration*, *Advanced configuration*, set keys by name and save them as a named configuration.
I wanted the IMU's raw samples, `ESF-RAW`, and kept the configuration as `UART1-Recording`:

<figure>
	<img src={ucenter} alt="u-center 2's Device configuration window, Advanced configuration, with the saved configuration UART1-Recording. Key CFG-MSGOUT-UBX_ESF_RAW_UART1 is selected, value 50, with layers RAM 50, Flash 50 and Default 0 listed under it. The list of configuration changes sets each of CFG-UART1OUTPROT-UBX to 1, CFG-UART1OUTPROT-NMEA to 0, CFG-UART1-BAUDRATE to 115200, CFG-MSGOUT-UBX_ESF_RAW_UART1 to 50 and CFG-NAV2-OUT_ENABLED to 1, each in the RAM, BBR and Flash layers." width="1634" height="977" />
	<figcaption>The configuration in u-center 2: fifteen changes, five keys each written to RAM, BBR and flash.</figcaption>
</figure>

It sets five keys, each in all three layers: RAM, BBR and flash.
Their meanings are from the interface description, §6.9.9 (`CFG-MSGOUT`) and §6.9.10 (`CFG-NAV2`).

| key                            | value  | what it does                                  |
| ------------------------------ | -----: | --------------------------------------------- |
| `CFG-UART1OUTPROT-UBX`         |      1 | UBX output on UART1                           |
| `CFG-UART1OUTPROT-NMEA`        |      0 | no NMEA output on UART1                       |
| `CFG-UART1-BAUDRATE`           | 115200 | UART1's baud rate                             |
| `CFG-MSGOUT-UBX_ESF_RAW_UART1` |     50 | `ESF-RAW` output on UART1                     |
| `CFG-NAV2-OUT_ENABLED`         |      1 | the secondary, GNSS-only output (NAV2)        |

**What to look for.** That u-center accepts each change, and that the key shows its new value in each layer it was written to.

**What I learned.**
- **Each port is configured on its own.** These keys change UART1 only: its protocols, its baud rate, and which messages go out on it.
  USB keeps its own settings and still sends NMEA.
- **A message's rate is per port.** `CFG-MSGOUT-UBX_ESF_RAW_UART1` turns `ESF-RAW` on for UART1 alone.
  Every message has one such key for each port.
- **Configuration has layers.** RAM is lost at power-off, BBR lasts while a backup supply holds, and flash is permanent.
  Writing to flash, as here, makes the change survive a power cycle, but it also means the board no longer starts from its defaults.
  The box itself will write RAM and BBR only, and touch flash only after asking.
- **A GUI is a fine way in.** u-center showed me which settings exist before I knew what to ask for, and the keys it set are the same ones a script will set later.
- **The baud rate is the line's speed, and both ends must agree on it.** It counts the signal changes per second on the wire.
  With the usual framing of 8 data bits plus a start and a stop bit, each byte takes 10 of them, so 115200 baud carries at most 11 520 bytes a second.
  UART1 is now at 115200, and anything listening on it has to use the same rate.

## 3. Checking that bytes flow

**What it is for.** Confirming, before writing any code, that the pins are alive: that bytes come out of `TX1` at the baud rate just configured.

**How it is done.** Wire an FTDI USB-serial adapter to the board:

- the adapter's `RX` to the board's `TX1`, since one side's output is the other's input;
- the adapter's `GND` to the board's `GND`;
- the adapter's logic level matched to the board's IOREF.

IOREF is the voltage the UART pins swing between ground and.
A 3.3 V adapter that sees 5 V on its `RX` can be damaged, and so can a Raspberry Pi's GPIO, so this is worth checking before the first wire goes on.
On this board a slide switch beside the F9R module sets it:

<figure>
	<img src={ioref} alt="Close-up of the board beside the ZED-F9R module. A vertical slide switch is labelled IOREF = 3V3, 5V = OUTPUT at its top end and IOREF & 5V ARE INPUTS at its bottom end. To its right, the IOREF LED (LED6) is lit blue and the NO RTK LED is lit red. Below, connector J4 is labelled PIXHAWK + POWER, with pins VIN, RX1, TX1, TPS, EVT and GND." width="1600" height="1200" />
	<figcaption>The IOREF switch. Its two positions are labelled <code>IOREF = 3V3, 5V = OUTPUT</code> and <code>IOREF &amp; 5V ARE INPUTS</code>.</figcaption>
</figure>

As the labels read, the two positions do this:

- **`IOREF = 3V3, 5V = OUTPUT`:** the board sets IOREF to 3.3 V itself, and supplies 5 V on its `5V` pin.
- **`IOREF & 5V ARE INPUTS`:** the connected hardware supplies both.
  That matches the sibling board's guide from step 1, which says IOREF must then be connected to the voltage the other hardware needs.

For a 3.3 V adapter, and later for the Pi, the first position is the one to want.
Confirm it with a meter on the `IOREF` pin before connecting anything.

On this board the switch is set to `IOREF = 3V3, 5V = OUTPUT`: the UART pins run at 3.3 V, and the board's `5V` pin supplies 5 V.
That is the pin the OpenLog draws its power from in step 5.

Plugged into the computer, the adapter appears as `/dev/ttyUSB0`.
It is a bridge chip: on one side it speaks UART, on the other USB, and Linux's `ftdi_sio` driver presents it as a serial port.
Open that port in picocom at UART1's baud rate:

```sh
picocom -b 115200 /dev/ttyUSB0      # exit with Ctrl+A, then Ctrl+X
```

<figure>
	<img src={picocom} alt="picocom v3.1 opened on /dev/ttyUSB0 at 115200 baud, 8 data bits, no parity, 1 stop bit, no flow control, escape Ctrl+A. After 'Terminal ready', lines of mostly unprintable characters shown as diamonds, with a lowercase b and a less-than sign recurring throughout." width="452" height="751" />
	<figcaption>UART1 through the FTDI adapter in picocom: binary UBX, shown as whatever characters happen to be printable.</figcaption>
</figure>

**What to look for.** A steady stream, and it will look like garbage.
UBX is binary, and a terminal can only show the bytes that happen to be printable.
The pattern still shows through: a `b` keeps recurring, followed shortly by `<`.
Every UBX frame starts with the two sync bytes `b5 62`, and `0x62` is the letter `b`.
An `ESF-RAW` frame carries a 60-byte payload, and 60 is `0x3c`, the character `<`.
So each `b … <` is the start of another IMU message.

**What I learned.**
- **Garbage that keeps coming is the answer here.** It says the pins are alive.
  A wrong baud rate also gives garbage, though, so the real confirmation comes when the bytes parse, in the next step.
- **The baud rate is real on an adapter.** An FTDI chip drives an actual UART at the rate it is given, so it has to match `CFG-UART1-BAUDRATE`.
- **`/dev/ttyUSB*` means a bridge chip.** The receiver's own USB port appears differently, as `/dev/ttyACM*`, and that is a story for the ledger's questions.

## 4. Recording a file and parsing it

**What it is for.** Turning the stream into something a program can check.
Garbage on a screen says bytes arrive.
A parser that finds valid messages in them says the baud rate, the wiring and the configuration are all right.

**How it is done.** Two short scripts, run from the repository root.

`tools/ubx-record.py` copies the port's bytes, unchanged, into a file, and prints a running count so you can see data is flowing:

<details>
<summary><code>tools/ubx-record.py</code>, in full</summary>

```python
"""Record a serial port's bytes, unchanged, into a file.

usage: ubx-record.py PORT OUT [--baud 115200] [--seconds N]

For a USB-serial adapter (FTDI, CP210x) wired to one of the F9R's UARTs, PORT is `/dev/ttyUSB0` and
the baud rate must match the UART's `CFG-UARTn-BAUDRATE`. Stops after `--seconds`, or on Ctrl+C,
and prints the byte count once a second so you can see data is flowing.
"""

import argparse
import sys
import time

import serial


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("port")
    ap.add_argument("out")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--seconds", type=float, help="stop after this long")
    args = ap.parse_args()

    total = 0
    start = time.monotonic()
    last_report = start
    # A short timeout keeps the loop responsive when the line is quiet.
    with serial.Serial(args.port, args.baud, timeout=0.2) as port, open(args.out, "wb") as out:
        print(f"recording {args.port} at {args.baud} baud into {args.out}; Ctrl+C to stop")
        try:
            while args.seconds is None or time.monotonic() - start < args.seconds:
                chunk = port.read(4096)
                out.write(chunk)
                total += len(chunk)
                now = time.monotonic()
                if now - last_report >= 1.0:
                    elapsed = now - start
                    print(f"  {elapsed:6.1f} s  {total:>10} bytes  ({total / elapsed:,.0f} B/s)")
                    last_report = now
        except KeyboardInterrupt:
            pass
    elapsed = time.monotonic() - start
    print(f"wrote {total} bytes in {elapsed:.1f} s to {args.out}")
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
```

</details>

`tools/ubx-parse.py` reads the file with pyubx2 and counts the messages of each kind.
It also counts the errors the parser hit, and prints the last few messages. pyubx2 leaves `ESF-RAW`'s data words as raw bytes, so the script decodes those itself, from the layout in step 1's figure:

<details>
<summary><code>tools/ubx-parse.py</code>, in full</summary>

```python
"""Parse a file of raw receiver output and say what is in it.

usage: ubx-parse.py FILE [--last N]

FILE is anything that holds the bytes a u-blox port sent: a recording from ubx-record.py, or an
OpenLog `LOGnnnnn.TXT`. Prints how many messages of each kind were parsed, how many errors the
parser hit, and the last N messages, formatted.

`UBX-ESF-RAW` is decoded here because pyubx2 leaves its data words as bytes. In each 8-byte group,
bits 23..0 of the data word are the value and bits 31..24 its type, followed by a U4 time tag
(u-blox F9 HPS 1.30 Interface Description, UBX-22010984 R03, §3.11.4). Types and scales are from the
ZED-F9R Integration Manual, UBX-20039643 R10, Table 15.
"""

import argparse
import sys
from collections import Counter, deque

from pyubx2 import ERR_LOG, NMEA_PROTOCOL, UBX_PROTOCOL, UBXReader

# dataType -> (name, unit, scale); all signed 24-bit (Integration Manual R10, Table 15).
ESF_TYPES = {
    5: ("gyro_z", "deg/s", 2**-12),
    12: ("gyro_temp", "degC", 1e-2),
    13: ("gyro_y", "deg/s", 2**-12),
    14: ("gyro_x", "deg/s", 2**-12),
    16: ("accel_x", "m/s^2", 2**-10),
    17: ("accel_y", "m/s^2", 2**-10),
    18: ("accel_z", "m/s^2", 2**-10),
}


def esf_raw(raw: bytes) -> str:
    payload = raw[6:-2]
    parts = []
    for k in range(4, len(payload) - 7, 8):
        word = int.from_bytes(payload[k : k + 4], "little")
        value = word & 0xFFFFFF
        if value & 0x800000:
            value -= 1 << 24
        name, unit, scale = ESF_TYPES.get(word >> 24, (f"type{word >> 24}", "", 1.0))
        parts.append(f"{name:>9} = {value * scale:+9.4f} {unit}")
    sttag = int.from_bytes(payload[8:12], "little") if len(payload) >= 12 else None
    return f"ESF-RAW  sTtag={sttag}\n    " + "\n    ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--last", type=int, default=2, help="how many messages to print (default 2)")
    args = ap.parse_args()

    errors: list[str] = []
    counts: Counter[str] = Counter()
    last: deque[tuple[bytes, object]] = deque(maxlen=args.last)

    with open(args.file, "rb") as f:
        size = f.seek(0, 2)
        f.seek(0)
        reader = UBXReader(
            f,
            protfilter=UBX_PROTOCOL | NMEA_PROTOCOL,
            quitonerror=ERR_LOG,
            errorhandler=lambda e: errors.append(str(e)),
        )
        for raw, msg in reader:
            if msg is None:
                continue
            counts[msg.identity] += 1
            last.append((raw, msg))

    print(f"{args.file}: {size} bytes")
    print(f"parsed {sum(counts.values())} messages, {len(errors)} errors")
    for identity, n in counts.most_common():
        print(f"  {identity:<10} {n:>10}")
    for e, n in Counter(errors).most_common(3):
        print(f"  error x{n}: {e}")
    if last:
        print(f"last {len(last)}:")
    for raw, msg in last:
        print("  " + (esf_raw(raw) if msg.identity == "ESF-RAW" else str(msg)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

</details>

```sh
pixi run python tools/ubx-record.py /dev/ttyUSB0 uart1.ubx --seconds 10
pixi run python tools/ubx-parse.py uart1.ubx --last 2
```

Close picocom first: only one program at a time can hold the port.

**What to look for.**
- **`ESF-RAW` counted in the hundreds**, which means the bytes parse.
- **A few `GNTXT` lines.** They are NMEA text messages, sent even with NMEA output off.
- **Few errors.** The recording stops wherever Ctrl+C or `--seconds` lands, usually partway through a frame, so one cut-short frame at the end is expected.
- **Plausible values in the last messages.** With the board lying flat, `accel_z` should be near gravity and the gyro rates near zero.

**What came out.** One ten-second run:

<figure>
	<img src={step4} alt="A terminal. ubx-record.py records /dev/ttyUSB0 at 115200 baud into uart1.ubx for 10 seconds, printing a count each second from 6647 bytes at 1.0 s to 65883 bytes at 10.0 s, about 6,600 to 6,700 bytes a second, and writes 65883 bytes. ubx-parse.py then reports uart1.ubx at 65883 bytes, 969 messages parsed with 3 errors: 959 ESF-RAW and 10 GNTXT. Two errors read: Message checksum b'<\x00' invalid - should be b'k*'. One reads: Serial stream terminated unexpectedly, 62 bytes requested, 36 bytes returned. The last two ESF-RAW messages, sTtag 7608858 and 7609115, show accel_z +10.4746 m/s^2, gyro rates within about half a degree per second of zero, and gyro_temp about 33.2 degC." width="820" height="671" />
	<figcaption>Step 4 on the bench: ten seconds of UART1 recorded through the FTDI adapter, then parsed.</figcaption>
</figure>

- **The bytes parse.** In 10.0 s the recorder wrote 65 883 bytes, between 6 586 and 6 728 a second.
  The parser found 969 messages in them: 959 `ESF-RAW` and 10 `GNTXT`.
- **There were three errors, not one.** One is the expected cut-short frame at the end: 62 bytes requested, 36 returned.
  The other two are checksum failures, and the bytes the parser read as each checksum, `3c 00`, are how every `ESF-RAW` frame's length field begins.
  So in those two places the next frame started before the current one had ended: bytes went missing in the middle of the stream.
  This run doesn't say where they were lost, in the receiver, on the wire or in the computer.
- **The values are plausible.** The last two messages read `accel_z` = +10.4746 m/s², the gyro rates within half a degree per second of zero, and a gyro temperature of about 33 °C, with consecutive time tags 7 608 858 and 7 609 115.

**What I learned.**
- **The whole chain works.** Configuration, wiring, baud rate and parser all agree, because hundreds of messages decode cleanly.
- **The line is about half full.** About 6 600 bytes a second, against the 11 520 that 115200 baud can carry.
- **A parser's error count is information.** A checksum failure here doesn't mean the parser is wrong.
  It means bytes were lost, and a recorder that keeps the box's data has to notice that, not skip past it.
- **Raw IMU values are raw.** `accel_z` reads about 10.47 m/s², where gravity alone would give about 9.8.
  `ESF-RAW` carries the sensor's output before any calibration, and the gyro runs warm, at about 33 °C.

> [!TODO]
> Correct these in your own words, and add what surprised you.

## 5. Recording with the OpenLog

**What it is for.** Recording without a computer.
I had a SparkFun OpenLog sitting around, so it was the natural next step: a logger that can travel with the board.

**How it is done.** Wire the OpenLog in place of the adapter:

- yellow from `TX1` to the OpenLog's `RX`;
- green from the OpenLog's `TX` to `RX1`;
- red to 5 V, from the top header's `5V IN/OUT` pin, to power it;
- blue to `GND`.

Set the OpenLog to the same baud rate, in the `config.txt` on its card.
The file is two lines: the settings, comma-separated, and below them the name of each.
The first, `baud`, is the one that matters here, and it has to match `CFG-UART1-BAUDRATE`:

```text
115200,26,3,0,1,1,0
baud,escape,esc#,mode,verb,echo,ignoreRX
```

Before the card goes into the OpenLog, it holds nothing else:

<figure>
	<img src={openlogConfig} alt="Left, a terminal running cat /mnt/sdcard/config.txt, which prints two lines: 115200,26,3,0,1,1,0 and baud,escape,esc#,mode,verb,echo,ignoreRX. Right, a file manager open at /mnt/sdcard/ showing a single file, config.txt." width="1129" height="264" />
	<figcaption>The SD card mounted on the computer before it goes into the OpenLog: <code>config.txt</code> and nothing else.</figcaption>
</figure>

As it records, the OpenLog writes its log files next to `config.txt`, numbered `LOG00001.TXT`, `LOG00002.TXT` and so on.

Power the board, let it record, then take the card out and parse its file with the same script:

```sh
pixi run python tools/ubx-parse.py LOG00001.TXT --last 2
```

> [!TODO]
> Run it on one of the card's logs, and paste the output or a screenshot here.

**What to look for.** The same message kinds as step 4, in larger numbers, since the logger runs for as long as it has power.

**What I learned.**
- **An SD logger needs no computer, but it has no clock.** The file holds the bytes and nothing else.
  A recording through the adapter, by contrast, could stamp each read with the computer's time.
  That matters later, because some of the ledger's questions are about timing.
- **Green carries the OpenLog's output into the receiver's `RX1`.** Whatever the OpenLog transmits reaches UART1's input, so that wire should come off if UART1 is ever wired to anything else.

> [!TODO]
> Add anything else, in your own words.

## What comes next

With data flowing from the pins into a file and a parser, the ledger's questions about the receiver become things to try rather than things to read about.
The first ones this sets up:

- [#1](../../reference/open-questions/index.md#blocking-m1), which firmware the receiver runs: poll `UBX-MON-VER`.
- [#11](../../reference/open-questions/index.md#blocking-m2), the IMU's sample rate and how `ESF-RAW` frames it: steps 4 and 5 already show the framing, and a recording through the adapter can time it.
- [#14](../../reference/open-questions/index.md#blocking-m2), whether a logger and the Pi conflict on the receiver's ports: this lab puts the logger on UART1.
