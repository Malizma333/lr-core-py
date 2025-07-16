function captureState() {
  const state = [];
  const index = Math.floor(store.getState().player.index);
  state.push(parseInt(store.getState().trackData.version[2]));
  state.push(index);
  state.push(0);
  state.push(0);
  state.push(
    store.getState().trackData.riders.map(rider => ({
      position_x: rider["startPosition"]["x"],
      position_y: rider["startPosition"]["y"],
      velocity_x: rider["startVelocity"]["x"],
      velocity_y: rider["startVelocity"]["y"],
      angle: rider["startAngle"] || 0,
      remount: rider["remountable"] === 1,
    })),
  );
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
