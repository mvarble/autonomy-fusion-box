---
title: "Inspect the ArduSimple RTK board"
pages: []
---

This probe connects to the ArduSimple ZED-F9R board and closes the open questions about it that a
single reading can settle: which firmware it runs (question 1), and the IMU's sample rate and
message framing (question 11). The firmware comes first, because every configuration key and the
UBX protocol the box will use depend on it. The probe only polls the receiver and records what it
returns; it changes no configuration and writes nothing to flash.
