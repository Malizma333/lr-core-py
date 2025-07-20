// Utility to download track state from linerider.com for test case usage

function captureState(testName) {
  const state = [];
  const index = Math.floor(store.getState().player.index);
  state.push(testName);
  state.push(index);
  state.push(store.getState().trackData.label);
  const formatNumber = (n) => n.toPrecision(17).replace(/\.?0+$/, "");
  // peg, tail, nose, string, butt, shoulder, rhand, lhand, lfoot, rfoot, scarf0...6
  state.push(
    store.getState().simulator.engine.getFrame(index).snapshot.entities[0].entities.map(entity =>
      entity.points.map(
        point => [
          formatNumber(point.pos.x),
          formatNumber(point.pos.y),
          formatNumber(point.vel.x),
          formatNumber(point.vel.y),
        ],
      )
    ),
  );

  return JSON.stringify(state) + ",";
}
