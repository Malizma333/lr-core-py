from __future__ import annotations
from typing import Union
from engine.vector import Vector
from engine.entity import RiderVehiclePair
from engine.grid import Grid, GridVersion
from engine.line import Line
from engine.constants import (
    DEFAULT_CELL_SIZE,
    GRAVITY_SCALAR,
    GRAVITY_SCALAR_V67,
    ITERATIONS,
)


class CachedFrame:
    def __init__(self, entities: list[RiderVehiclePair]):
        self.entities: list[RiderVehiclePair] = entities


# Not specific implementation, just used for caching
class Engine:
    def __init__(
        self,
        grid_version: GridVersion,
        entities: list[RiderVehiclePair],
        lines: list[Line],
    ):
        self.grid = Grid(grid_version, DEFAULT_CELL_SIZE)
        self.gravity_vector = Vector(0, 1)
        self.state_cache: list[CachedFrame] = [
            CachedFrame([entity.copy() for entity in entities])
        ]

        self.gravity_scale = GRAVITY_SCALAR
        if grid_version == GridVersion.V6_7:
            self.gravity_scale = GRAVITY_SCALAR_V67

        for line in lines:
            self.grid.add_line(line)

    def get_frame(self, target_frame: int) -> Union[CachedFrame, None]:
        if target_frame < 0:
            return None

        for frame in range(len(self.state_cache), target_frame + 1):
            new_entities: list[RiderVehiclePair] = []

            for entity in self.state_cache[frame - 1].entities:
                new_entities.append(entity.copy())

            for entity in new_entities:
                # gravity + momentum
                entity.process_initial_step(self.gravity_scale * self.gravity_vector)

                for _ in range(ITERATIONS):
                    # bones
                    entity.process_bones()
                    # line collisions
                    entity.process_collisions(self.grid)

                # scarf
                entity.process_flutter()

                # dismount or break sled
                entity.process_joints()

            self.state_cache.append(CachedFrame(new_entities))

        return self.state_cache[target_frame]

    # Primitive add and remove line methods
    # A proper implementation would look through the grid to optimize cache clears
    def add_line(self, line: Line):
        line.base.id = self.grid.get_max_line_id() + 1
        self.state_cache = [self.state_cache[0]]
        self.grid.add_line(line)

    def remove_line(self, id: int):
        line = self.grid.get_line_by_id(id)
        if line != None:
            self.state_cache = [self.state_cache[0]]
            self.grid.remove_line(line)
