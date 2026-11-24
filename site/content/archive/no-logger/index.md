---
title: "Record everything on the Pi, without an SD logger"
pages:
    - start/what-the-box-is
    - reference/milestones
    - reference/open-questions
---

The box dropped its separate SD-card logger, the role the SparkFun OpenLog played in the rtk-inspection lab, and records everything on the Pi.
The receiver reaches the Pi over USB alone, which also carries its power, and UART1's output is turned off, so there is one data path, one recorder and one configuration to keep true.
The bags hold the raw IMU and GNSS observations, `ESF-RAW`, `RXM-RAWX` and `RXM-SFRBX`, as datasets for exploring fusion later, and `ubx_mux` writes the raw byte stream to a file that RTKLIB reads for PPK.
The cost is that nothing is recorded independently of the Pi.
The ledger settled #14 as decided, pointed #32 at the USB log, and gained two rows: whether the firmware sends the raw observations on USB (#33), and whether the microSD sustains the recorder's write rate (#34), measured in M5.
