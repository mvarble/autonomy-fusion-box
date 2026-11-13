---
title: "Inspect the ArduSimple RTK board"
pages: []
---

This probe is a first session with the ArduSimple ZED-F9R board. It starts by getting data out of
the board's pins: configuring UART1 in u-center 2 and recording what it sends with an SD logger,
the path the box keeps for its raw-UBX backup. It then closes the open questions a single reading
can settle: which firmware the receiver runs (question 1), and the IMU's sample rate and message
framing (question 11). The firmware matters first, because every configuration key and the UBX
protocol the box will use depend on it. After the first step, the probe only reads from the
receiver.
