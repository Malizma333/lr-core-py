# Line Rider Physics in Python

A compatible implementation of Line Rider's physics engine written in python. Despite the name, this is **not** a fork of lr-core and is structured entirely differently for ease of reference (see `/src/engine`). Nothing requires external dependencies.

Tests can be run with `src/test.py`.
A primitive track simulator can be run with `src/simulator.py`.

Thanks to:
- [lr-core](https://github.com/conundrumer/lr-core) for having nice test cases and class abstractions
- [LROverhaul](https://github.com/LunaKampling/LROverhaul) and [linerider-advanced](https://github.com/jealouscloud/linerider-advanced) for putting all the math in a few files
- [OpenLR](https://github.com/kevansevans/OpenLR) for showing clear differences in legacy grid algorithms
- [bosh-rs](https://codeberg.org/lipfang/bosh-rs) for motivating me to start working on this

Current features:
- 6.0, 6.1, 6.2 grid implementations
- 6.7 gravity fix
- rider bones, points, and bindings
- line extensions, flipped lines, acceleration multipliers

Planned TODOs:
- Scarf implementation (.com only, not worried about compatibility)
- Remount implementation (.com and LRO)
- Better API for adding, removing, and moving lines inside the grid + refreshing engine cache
