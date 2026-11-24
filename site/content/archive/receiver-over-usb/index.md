---
title: "Talk to the receiver over USB"
pages: []
---

A session at the bench with the receiver on USB to a computer, the path the box now uses for all of its data.
It polls `UBX-MON-VER` to learn which firmware the receiver runs, since every key the box sets depends on it (#1).
With the key list known, it turns on `RXM-RAWX` and `RXM-SFRBX` on USB in RAM only, reads the keys back, and counts each message in a short recording, to check that the raw observations PPK and the bags need arrive on that port (#33).
The same recording times `ESF-RAW` and shows how it frames the IMU's samples (#11), and its checksums give a first look at whether USB loses frames the way UART1 did (#32).
