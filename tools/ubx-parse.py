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
