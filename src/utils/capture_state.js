// Utility to download track state from linerider.com for test case usage

function captureState(testName, includeScarf = false, includeState = false) {
  const testData = {};
  const index = Math.floor(store.getState().player.index);
  testData["test"] = testName;
  testData["frame"] = index;
  testData["file"] = store.getState().trackData.label;
  const formatNumber = (n) => n.toPrecision(17).replace(/\.?0+$/, "");
  // peg, tail, nose, string, butt, shoulder, rhand, lhand, lfoot, rfoot, scarf0...6
  testData["state"] = {
    "entities": store.getState().simulator.engine.getFrame(index).snapshot.entities[0].entities.map(
      entity => {
        const entityState = {
          "points": entity.points.map(
            point => [
              formatNumber(point.pos.x),
              formatNumber(point.pos.y),
              formatNumber(point.vel.x),
              formatNumber(point.vel.y),
            ],
          ),
        };

        if (includeState) {
          entityState["rider_state"] = entity.riderState;
          entityState["sled_state"] = entity.sledState;
        }

        return entityState;
      },
    ),
  };

  if (!includeScarf) {
    for (let i = 0; i < testData["state"].entities.length; i++) {
      testData["state"].entities[i]["points"].splice(10, 7);
    }
  }

  return JSON.stringify(testData) + ",";
}
