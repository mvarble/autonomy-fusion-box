# fusion box

A portable, battery-powered box that records GNSS, IMU and camera data on one GPS-disciplined
timebase. Each milestone ends in a write-up with measured numbers.

The site is the project's record: what the box is, what is still unverified, and how each decision
was reached. It is published at <https://mvarble.github.io/autonomy-fusion-box/> on every push that
passes CI, from any branch, so it shows the latest push. To read it locally:

```sh
cd site && pnpm install && pnpm dev    # http://localhost:5173
```

`AGENTS.md` says how the work is done, and `site/README.md` how the site works.
