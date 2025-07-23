// Utility to download track state from linerider.com for test case usage

function captureState(testName, includeScarf = false) {
  const state = [];
  const index = Math.floor(store.getState().player.index);
  state.push(testName);
  state.push(index);
  state.push(store.getState().trackData.label);
  const formatNumber = (n) => { // compatible float precision formatter
    let number = n.toPrecision(17);
    const ind = number.indexOf("e")

    if (ind != -1) {
        const offset = parseInt(number.slice(ind + 2))
        number = "0." + Array(offset - 1).fill("0").join("") + number.charAt(0) + number.slice(2, ind)
    }

    return number.replace(/\.?0+$/, "");
  }
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

  if (!includeScarf) {
    for (let i = 0; i < state[3].length; i++) {
      state[3][i].splice(10, 7)
    }
  }

  return JSON.stringify(state) + ",";
}
