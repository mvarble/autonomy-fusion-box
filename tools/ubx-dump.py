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
