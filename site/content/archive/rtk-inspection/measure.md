---
summary: The ZED-F9R on the ArduSimple board runs firmware HPS 1.40, protocol version 33.40, read from `UBX-MON-VER` over USB; its old OpenLog recordings show `ESF-RAW` carries one 7-sample set per message, 257 time-tag ticks apart, but not yet what a tick is in seconds.
---

<script>
	import board from './board.jpg';
</script>

## What I set out to check

- [#1](../../reference/open-questions/index.md#blocking-m1): which firmware the F9R runs. Every
  configuration key the box will set, and which UBX messages exist, depend on it, so M1's config
  tool cannot be written against the right interface description until this is known.
- [#11](../../reference/open-questions/index.md): the IMU sample rate and how `ESF-RAW` frames it.

  How the samples are framed decides how M2's driver splits them into IMU messages. The rate
  decides the IMU noise model and the bag size.

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
- **The wires**, all four leaving through the enclosure wall:
  - **yellow:** `TX1`, on the bottom header;
  - **green:** `RX1`, beside it;
  - **red:** 5 V, at the top header's pin above `LED7` (`5V IN/OUT`);
  - **blue:** ground, at the end of the XBee socket's lower row.

  So UART1 and power go to the logger, and the F9R's UART1 output is what it records.
- **J4, a 6-pin JST connector labelled PIXHAWK + POWER**, at the right edge. Its pins read, from 1
  to 6: `VIN`, `RX1`, `TX1`, `TPS`, `EVT`, `GND`. So UART1, the timepulse and an event input are on
  one connector.
- **The bottom header** also carries `RX2`, `TX2`, `GEOFENCE`, `EXTINT`, `TPS`, `GND`, `RST`,
  `SDA` and `SCL`. There is a separate `TPS` pad labelled `J9` near the top.
- **A slide switch labelled XBEE TO GPS UART1 / XBEE TO GPS UART2** picks which of the F9R's UARTs
  the XBee socket reaches. It is set to XBEE TO GPS UART2, and the socket is empty.
- **A second slide switch** chooses between `IOREF = 3V3, 5V = OUTPUT` and
  `IOREF & 5V ARE INPUTS`.
- **The footprint labelled `BAT`** in the middle of the board, a circle with two pads, has nothing
  fitted.
- **LEDs:** `POWER` is lit, and so is `NO RTK`, in red. `PVT` is dark, and the photo was taken
  indoors. `5V IN/OUT`, `IOREF` and one of the `GPS>XBEE` / `XBEE>GPS` pair are lit as well.

The other end of the wires is a SparkFun OpenLog, a small board that writes whatever arrives on its
serial input to a file on an SD card. Its `config.txt`, verbatim:

```text
115200,26,3,0,1,1,0
baud,escape,esc#,mode,verb,echo,ignoreRX
```

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

I ran the script many times without keeping count. The reply quoted under Results is from one of
those runs.

**Along the way, picocom.** Opening the same port in picocom showed NMEA sentences flowing on USB
and no visible UBX. That is the board's stored configuration rather than a fault: I had earlier
configured UBX output on the board's UART pins, not on USB.

**Then the OpenLog's recordings.** The SD card held four logs, `LOG00001.TXT` to `LOG00004.TXT`,
from that earlier setup. I don't know when they were recorded or for how long, and the GPS antenna
was most likely not connected for any of them. They are what the F9R sent out of UART1, byte for
byte, with no timestamps of the OpenLog's own.

pyubx2 1.4.1 parses `ESF-RAW` but leaves each data word as raw bytes, so I wrote
`tools/ubx-dump.py`. It frames the byte stream itself, so that every byte is counted as a good UBX
frame, a bad-checksum frame, an NMEA sentence or a stray byte, and it decodes `ESF-RAW` from the
documents:

- the payload is a 4-byte reserved field, then repeated 8-byte groups, each a data word and a U4
  `sTtag` (`[ID §3.11.4]`);
- in the data word, bits 23…0 are `dataField` and bits 31…24 are `dataType` (`[ID §3.11.4]`);
- the types, their scales and their signedness come from `[IM]` Table 15 (§3.2.7.5).

`[ID]` is the u-blox F9 HPS 1.30 Interface Description, UBX-22010984 R03. `[IM]` is the ZED-F9R
Integration Manual, UBX-20039643, which its URL in the ledger served as revision R10 on 2026-11-13.

`pixi run python tools/ubx-dump.py FILE` prints every message, `--only ESF-RAW` filters, and
`--summary` prints the totals quoted below. I ran `--summary` once on each log.

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

### The OpenLog recordings

`--summary` on each log:

| log            |      bytes | `ESF-RAW` | `GNTXT` | bad-checksum frames | stray bytes |
| -------------- | ---------: | --------: | ------: | ------------------: | ----------: |
| `LOG00001.TXT` |    179 473 |     2 628 |      22 |                   0 |          21 |
| `LOG00002.TXT` | 39 260 528 |   574 394 |   5 933 |                   0 |          14 |
| `LOG00003.TXT` | 17 748 762 |   259 676 |   2 670 |                   0 |          14 |
| `LOG00004.TXT` |  4 773 308 |    69 839 |     713 |                   0 |          14 |

Every byte is accounted for:

- **The stray bytes** in each log are its last frame, cut off: the file ends partway through an
  `ESF-RAW` that starts `b5 62 10 03 3c 00`.
- **Every `GNTXT` sentence** reads `$GNTXT,01,01,00,txbuf alloc S*12`. Neither document I searched
  explains that text.
- **No other message** is in any log.

**Framing.** All 906 537 `ESF-RAW` messages have the same seven samples, in the same order:

| `dataType` | meaning (`[IM]` Table 15)       | scale         |
| ---------: | ------------------------------- | ------------- |
|         16 | x-axis accelerometer            | m/s² · 2⁻¹⁰   |
|         17 | y-axis accelerometer            | m/s² · 2⁻¹⁰   |
|         18 | z-axis accelerometer            | m/s² · 2⁻¹⁰   |
|         14 | x-axis gyroscope                | deg/s · 2⁻¹²  |
|         13 | y-axis gyroscope                | deg/s · 2⁻¹²  |
|          5 | z-axis gyroscope                | deg/s · 2⁻¹²  |
|         12 | gyroscope temperature           | °C · 10⁻²     |

In every message all seven samples carry the same `sTtag`.

**The step in `sTtag` from one message to the next**, in ticks:

| log            | steps   |  min |  p1 |  p50 |  p99 | p99.9 |   max | steps over 1.5 × p50 | messages missing, about |
| -------------- | ------- | ---: | --: | ---: | ---: | ----: | ----: | -------------------: | ----------------------: |
| `LOG00001.TXT` | 2 627   |  156 | 228 |  257 |  514 | 1 546 | 1 801 |        49 (1.87 %)  |              71 (2.63 %) |
| `LOG00002.TXT` | 574 393 |  156 | 228 |  257 |  515 | 1 543 | 2 059 |    13 994 (2.44 %)  |          22 087 (3.70 %) |
| `LOG00003.TXT` | 259 675 |  158 | 228 |  257 |  515 | 1 520 | 2 059 |     6 387 (2.46 %)  |           9 125 (3.39 %) |
| `LOG00004.TXT` | 69 838  |  156 | 228 |  257 |  515 | 1 513 | 1 802 |     1 681 (2.41 %)  |           2 353 (3.26 %) |

- **The usual step is 255 to 259 ticks.** 257 is the most common in every log.
- **Steps near 514, 771 and so on are whole multiples of it.** I read those as messages missing from
  the stream, since no frame is corrupt.
- **The "messages missing" column** rounds each long step to a multiple of the median and counts
  the multiples beyond one.

**`sTtag` wraps.** It runs backwards 9, 4 and 1 times in `LOG00002`, `LOG00003` and `LOG00004`,
and none in `LOG00001`. Each time, the backward step is 2²⁴ less a normal step, so although the
field is typed U4, it behaves as a 24-bit counter. The largest value seen is 16 776 997, just under
2²⁴ = 16 777 216. The script unwraps these steps before the statistics above.

**`reserved0` counts too.** As a little-endian U4 it never decreases in any log. Over each log,
the unwrapped `sTtag` span divided by the `reserved0` span is 25.7259, 25.7205, 25.7194 and
25.7222. So two counters in the message keep a steady ratio of about 25.72. The ratio also comes out
right only when the wraps are unwrapped, which confirms them.

**Two regularities I can't explain.**
- All four logs start at `sTtag` 6 518 to 6 527, and `reserved0` 2 745 to 2 819.
- `LOG00002`, `LOG00003` and `LOG00004` all end with `sTtag` between 1 710 103 and 1 710 362, after
  different numbers of wraps.

**The values** (means over each log; full spread in each summary):

| log            | \|accel\| (m/s²) | `gyro_x` (deg/s) | `gyro_y` (deg/s) | `gyro_z` (deg/s) | gyro temp (°C) |
| -------------- | ---------------: | ---------------: | ---------------: | ---------------: | -------------: |
| `LOG00001.TXT` |          10.4359 |          −0.0364 |          −0.4909 |          −0.0766 | 22.95 to 25.07 |
| `LOG00002.TXT` |          10.4679 |          −0.0605 |          −0.4320 |          +0.0172 | 21.34 to 33.05 |
| `LOG00003.TXT` |          10.5203 |          −0.0791 |          −0.4315 |          +0.0245 | 21.00 to 34.89 |
| `LOG00004.TXT` |          10.4820 |          −0.0664 |          −0.4481 |          +0.0156 | 20.86 to 31.89 |

> [!TODO]
> Where the raw logs live: they are in `sdcard/` at the repository root, untracked, about 60 MB.

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

- **The firmware has been updated since the module was made.** The module is marked
  `ZED-F9R-01B-00`, and `[IM]` lists that type with HPS 1.20. HPS 1.40 belongs to `ZED-F9R-04B-00`
  in the same table. Someone, at ArduSimple or earlier me, flashed newer firmware.
- **`ESF-RAW` is one complete IMU sample per message.** Three accelerometer axes, three gyro axes
  and the gyro temperature share one `sTtag`, so M2's driver can turn each message into one
  `sensor_msgs/Imu` without matching samples across messages. That matches what `[IM §3.2.7.6]`
  promises: "one sample of every data type per message".
- **`sTtag` is a 24-bit counter in a 32-bit field.** Anything that maps `sTtag` to GNSS time has to
  unwrap it, and it wraps every 2²⁴ ticks. How long that is in seconds is still unknown.
- **The rate in Hz is not known yet.** The logs carry no clock of the OpenLog's, and neither
  document gives the unit of `ESF-RAW.sTtag`. The 1 ms resolution `[IM §3.2.5.2]` states is for
  `ESF-MEAS`, not `ESF-RAW`. One host-clocked capture, the unwrapped `sTtag` span over wall-clock
  time, would give both the tick and the rate. Counting messages per second would undercount by the
  dropped messages.
- **About 3 % of the messages never reached the card.** That is with zero corrupt frames, at 115200
  baud, which tells me UART1 was set to 115200 to match the OpenLog. The default is 38400
  `[IM §3.1.3]`. The `txbuf alloc S` warnings look related, but they don't line up with the gaps,
  so I can't say what they mean. Whatever records `ESF-RAW` has to expect gaps and detect them from
  `sTtag`, not assume a fixed rate.
- **The accelerometer reads high.** The magnitude of the acceleration vector, averaged over each
  log, is 10.44 to 10.52 m/s², where gravity alone would give about 9.8. That is raw data, uncorrected for scale or bias, and the gyro
  y-axis sits at about −0.43 to −0.49 deg/s. Neither is a calibration, but both are what M6 will
  have to remove.

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
  is on both J4 and the bottom header, and a switch connects the XBee socket to UART1 or UART2. As
  found, the OpenLog was on UART1 and the switch gave the empty XBee socket UART2.
- [#11](../../reference/open-questions/index.md#blocking-m2) stays **OPEN**. The framing is
  answered: one sample of each of the seven types per message, with one shared `sTtag`, the usual
  step 257 ticks. The rate in Hz waits for a host-clocked capture.
- [#10](../../reference/open-questions/index.md#blocking-m2) and
  [#13](../../reference/open-questions/index.md#blocking-m2) stay **OPEN**, with one new fact for
  both: `sTtag` wraps at 2²⁴.
- Opens [#33](../../reference/open-questions/index.md#blocking-m2): why about 3 % of `ESF-RAW`
  messages are missing from the UART recordings, and what `txbuf alloc S` means.
