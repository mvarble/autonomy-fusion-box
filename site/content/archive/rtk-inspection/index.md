---
title: "Inspect the ArduSimple RTK board"
pages:
    - reference/how-the-work-is-done
    - reference/milestones
    - reference/open-questions
    - start/what-the-box-is
---

A hands-on warm-up with the ArduSimple ZED-F9R board, before working through the ledger's open questions about it, written as a lab that someone new to embedded work can follow.
It finds the board's and the chip's documentation, configures UART1 in u-center 2 to send the IMU's raw samples, and checks that bytes flow through an FTDI adapter.
It then records UART1 to a file and parses it, first through the adapter and then with an SD-card logger, and finally looks at the signal itself on an oscilloscope and logic analyzer.
Every recording parsed, and the line's high level read 3.154 V, as the 3.3 V IOREF setting predicts.
A few frames arrived cut short in the middle of each recording, which opened a new question in the ledger.
Along the way the site gained images that open enlarged when clicked, and its pages moved to one sentence per line.
