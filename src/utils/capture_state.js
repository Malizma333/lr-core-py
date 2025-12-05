// Utility to download track state from linerider.com for test case usage
function captureState(testName, includeScarf = false, includeState = false) {
  const testData = {};
  const index = Math.floor(store.getState().player.index);
  testData["test"] = testName;
  testData["frame"] = index;
  testData["file"] = store.getState().trackData.label;

  // Convert f64 to hex (e.g. 0.45041712406070217 -> 0x3fdcd3a258598ab3)
  function f64ToHex(n) {
    const buffer = new ArrayBuffer(8);
    const view = new DataView(buffer);
    view.setFloat64(0, n, false); // false = big-endian
    const bytes = Array.from(new Uint8Array(buffer));
    return bytes.map(b => b.toString(16).padStart(2, "0")).join("");
  }

  // Order: peg, tail, nose, string, butt, shoulder, rhand, lhand, lfoot, rfoot, scarf0...6
  testData["state"] = {
    entities: store
      .getState()
      .simulator.engine.getFrame(index)
      .snapshot.entities[0].entities.map((entity) => {
        const entityState = {
          // Concatenate f64 hex strings (position x, position y, velocity x, velocity y)
          points: entity.points.map((point) =>
            f64ToHex(point.pos.x)
            + f64ToHex(point.pos.y)
            + f64ToHex(point.vel.x)
            + f64ToHex(point.vel.y)
          ),
        };

        if (includeState) {
          if (entity.riderState === undefined) {
            if (entity.riderMounted) {
              entityState["mount_state"] = "MOUNTED";
            } else {
              entityState["mount_state"] = "DISMOUNTED";
            }
          } else {
            entityState["mount_state"] = entity.riderState;
          }
          if (entity.sledState === undefined) {
            if (entity.sledIntact) {
              entityState["sled_state"] = "INTACT";
            } else {
              entityState["sled_state"] = "BROKEN";
            }
          } else {
            entityState["sled_state"] = entity.sledState;
          }
          entityState["rider_state"] = "INTACT";
        }

        return entityState;
      }),
  };

  if (!includeScarf) {
    for (let i = 0; i < testData["state"].entities.length; i++) {
      testData["state"].entities[i]["points"].splice(10, 7);
    }
  }

  return JSON.stringify(testData) + ",";
}
