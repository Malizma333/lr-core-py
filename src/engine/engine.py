from __future__ import annotations
from typing import Union
from engine.vector import Vector
from engine.entity import Entity
from engine.grid import Grid, GridVersion
from engine.line import PhysicsLine
from engine.constants import (
    DEFAULT_CELL_SIZE,
    GRAVITY_SCALAR,
    GRAVITY_SCALAR_V67,
    ITERATIONS,
)

# TODO: Review files for python-specific features


# Not specific implementation, just used for caching
class Engine:
    def __init__(
        self,
        grid_version: GridVersion,
        entities: list[Entity],
        lines: list[PhysicsLine],
    ):
        self.grid = Grid(grid_version, DEFAULT_CELL_SIZE)
        self.gravity_vector = Vector(0, 1)
        self.state_cache: list[list[Entity]] = [
            [entity.deep_copy() for entity in entities]
        ]

        self.gravity_scale = GRAVITY_SCALAR
        if grid_version == GridVersion.V6_7:
            self.gravity_scale = GRAVITY_SCALAR_V67

        for line in lines:
            self.grid.add_line(line)

    def get_frame(self, target_frame: int) -> Union[list[Entity], None]:
        if target_frame < 0:
            return None

        if target_frame < len(self.state_cache):
            return self.state_cache[target_frame]

        for frame in range(len(self.state_cache) - 1, target_frame):
            new_entities: list[Entity] = []

            for entity in self.state_cache[frame]:
                new_entities.append(entity.deep_copy())

            # track gravity + entity momentum
            for entity in new_entities:
                entity.process_initial_step(self.gravity_scale * self.gravity_vector)

            for i in range(ITERATIONS):
                for entity in new_entities:
                    # entity bones
                    entity.process_structural_bones()

                for entity in new_entities:
                    # entity-line collisions
                    entity.process_collisions(self.grid)

            for entity in new_entities:
                entity.process_flutter_bones()

            for entity in new_entities:
                entity.process_bind_triggers()

            self.state_cache.append(new_entities)

        return self.state_cache[target_frame]
