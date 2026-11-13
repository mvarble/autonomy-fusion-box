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
