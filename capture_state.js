// Utility to download track state from linerider.com for test case usage

function captureState() {
  const state = [];
  const index = Math.floor(store.getState().player.index);
  state.push(parseInt(store.getState().trackData.version[2]));
  state.push(index);
  state.push(6);
  state.push(22);
  state.push(store.getState().trackData.label);
  state.push(
    store.getState().simulator.engine.getFrame(index).snapshot.entities[0].entities.map(entity => ({
      points: entity.points.map(point => ({
        position_x: point.pos.x,
        position_y: point.pos.y,
        velocity_x: point.vel.x,
        velocity_y: point.vel.y,
      })),
    })),
  );
  return JSON.stringify(state);
}
