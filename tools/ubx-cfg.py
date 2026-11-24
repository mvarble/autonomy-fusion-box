"""Poll the F9R's firmware, read configuration keys, and set them in RAM only.

usage:
  ubx-cfg.py PORT ver                              poll UBX-MON-VER
  ubx-cfg.py PORT get KEY ... [--layer LAYER]      VALGET; LAYER is ram (default), bbr, flash, default
  ubx-cfg.py PORT set KEY=VALUE ...                VALSET in RAM only, then VALGET to read it back

Keys are written as u-blox writes them, e.g. CFG-MSGOUT-UBX_RXM_RAWX_USB. On USB, PORT is the
receiver's own CDC-ACM device (`/dev/ttyACM0`), and no baud rate applies. Only one program can hold
the port, so close u-center 2 first.

`set` writes the RAM layer and nothing else: what it sets is gone at the next power cycle. There is
deliberately no way to write BBR or flash from here.

Every request and response is also appended, as raw bytes, to `--log` (default `ubx-cfg.ubx`), so
the receiver's own answer is kept, not only this script's reading of it.
"""

from __future__ import annotations

import argparse
import sys
import time

import serial
from pyubx2 import POLL_LAYER_BBR, POLL_LAYER_DEFAULT, POLL_LAYER_FLASH, POLL_LAYER_RAM
from pyubx2 import SET_LAYER_RAM, TXN_NONE, UBXMessage, UBXReader

LAYERS = {
    "ram": POLL_LAYER_RAM,
    "bbr": POLL_LAYER_BBR,
    "flash": POLL_LAYER_FLASH,
    "default": POLL_LAYER_DEFAULT,
}


def key_name(key: str) -> str:
    """pyubx2 names keys with underscores where u-blox uses hyphens."""
    return key.replace("-", "_")


def exchange(port: serial.Serial, log, msg: UBXMessage, wanted: set[str], timeout: float = 3.0):
    """Sends `msg` and returns the first reply whose identity is in `wanted`, skipping the
    messages the receiver streams meanwhile. Returns None on timeout."""
    port.reset_input_buffer()
    raw = msg.serialize()
    log.write(raw)
    port.write(raw)
    reader = UBXReader(port, protfilter=2)  # UBX only
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        raw_reply, reply = reader.read()
        if reply is None:
            continue
        if reply.identity in wanted:
            log.write(raw_reply)
            return reply
    return None


def ack(port, log, msg: UBXMessage) -> str:
    reply = exchange(port, log, msg, {"ACK-ACK", "ACK-NAK"})
    return reply.identity if reply else "no reply"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("port")
    ap.add_argument("command", choices=["ver", "get", "set"])
    ap.add_argument("items", nargs="*", help="keys for get, KEY=VALUE for set")
    ap.add_argument("--layer", choices=LAYERS, default="ram", help="the layer get reads")
    ap.add_argument("--log", default="ubx-cfg.ubx", help="raw requests and responses, appended")
    args = ap.parse_args()

    with serial.Serial(args.port, 115200, timeout=0.5) as port, open(args.log, "ab") as log:
        if args.command == "ver":
            reply = exchange(port, log, UBXMessage("MON", "MON-VER", 2), {"MON-VER"})
            print(reply if reply else "no MON-VER reply")
            return 0 if reply else 1

        if args.command == "get":
            keys = [key_name(k) for k in args.items]
            failed = False
            # One key per poll, so that a key this firmware lacks is named by its own NAK.
            for key in keys:
                poll = UBXMessage.config_poll(LAYERS[args.layer], 0, [key])
                reply = exchange(port, log, poll, {"CFG-VALGET", "ACK-NAK"})
                if reply is None or reply.identity == "ACK-NAK":
                    print(f"{key}: {'NAK' if reply else 'no reply'} ({args.layer})")
                    failed = True
                else:
                    print(f"{key} = {getattr(reply, key, '?')} ({args.layer})")
            return 1 if failed else 0

        pairs = []
        for item in args.items:
            key, _, value = item.partition("=")
            pairs.append((key_name(key), int(value, 0)))
        result = ack(port, log, UBXMessage.config_set(SET_LAYER_RAM, TXN_NONE, pairs))
        print(f"VALSET to RAM: {result}")
        failed = result != "ACK-ACK"
        for key, value in pairs:
            reply = exchange(port, log, UBXMessage.config_poll(POLL_LAYER_RAM, 0, [key]), {"CFG-VALGET", "ACK-NAK"})
            got = getattr(reply, key, None) if reply and reply.identity == "CFG-VALGET" else None
            ok = got == value
            failed |= not ok
            print(f"  {key}: set {value}, read back {got} {'ok' if ok else 'MISMATCH'}")
        return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
