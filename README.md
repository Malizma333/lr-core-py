# Line Rider Physics in Python

A compatible implementation of Line Rider's physics engine written in python. Despite the name, this is **not** a fork of lr-core and is structured entirely differently for ease of reference. Nothing requires external dependencies.

Tests can be run with `src/test.py`.\
A primitive track simulator can be run with `src/simulator.py`.

Thanks to:
- [lr-core](https://github.com/conundrumer/lr-core) for having nice test cases and class abstractions
- [LROverhaul](https://github.com/LunaKampling/LROverhaul) and [linerider-advanced](https://github.com/jealouscloud/linerider-advanced) for putting all the math in a few files
- [OpenLR](https://github.com/kevansevans/OpenLR) for showing clear differences in legacy grid algorithms
- [bosh-rs](https://codeberg.org/lipfang/bosh-rs) for motivating me to start working on this

## Features
- beta 6.0, 6.1, 6.2 grid implementations
- beta 6.3 / 6.7 gravity fix
- line properties
  - line extensions
  - flipped lines
  - acceleration multipliers
- rider physics
  - multiple riders
  - flash scarf physics
  - linerider.com scarf physics (approximation)
  - lra:ce remounting
  - linerider.com remounting
    - with multipler riders

## Planned
- modded line types
  - windboxes
  - deceleration
  - trapdoor
  - double hitbox

# License

This project is licensed with GPL to remain compliant with LRA's GPL license, since it was used as a reference. Any modification or reference of this project must also be GPL-licensed and remain open source. See the [licenses directory](LICENSES/) for the full list of included licenses.

Some track fixtures sampled from the following:
- [Phunner](https://www.youtube.com/watch?v=Ak2_7jHtRpA) (6.7 gravity bug)
- [Wonky Walking](https://www.youtube.com/watch?v=E2-tvct-MpE) (linerider.com remount physics)
- [Bolted to the Wall](https://www.youtube.com/watch?v=0TBGNxzdiHw) (6.0 grid compatibility)
- [lr-core fixtures](https://github.com/conundrumer/lr-core/tree/master/fixtures) (6.1 compatibility, feature tests)
- [Fakie Park (Autumn's Section)](https://www.youtube.com/watch?v=tXJnpCyGOgk) (LRA remount physics)
