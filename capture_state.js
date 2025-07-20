// Utility to download track state from linerider.com for test case usage

function captureState(testName) {
  const state = [];
  const index = Math.floor(store.getState().player.index);
  state.push(testName);
  state.push(index);
  state.push(store.getState().trackData.label);
  // peg, tail, nose, string, butt, shoulder, rhand, lhand, lfoot, rfoot, scarf0...6
  state.push(
    store.getState().simulator.engine.getFrame(index).snapshot.entities[0].entities.map(entity =>
      entity.points.map(
        point => [
          point.pos.x.toPrecision(21),
          point.pos.y.toPrecision(21),
          point.vel.x.toPrecision(21),
          point.vel.y.toPrecision(21),
        ]
      )
    ),
  );

  return JSON.stringify(state) + ",";
}
