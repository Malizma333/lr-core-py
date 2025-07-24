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


class CachedFrame:
    def __init__(self, entities: list[Entity]):
        self.entities: list[Entity] = entities


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
        self.state_cache: list[CachedFrame] = [
            CachedFrame([entity.deep_copy() for entity in entities])
        ]

        self.gravity_scale = GRAVITY_SCALAR
        if grid_version == GridVersion.V6_7:
            self.gravity_scale = GRAVITY_SCALAR_V67

        for line in lines:
            self.grid.add_line(line)

    def get_frame(self, target_frame: int) -> Union[CachedFrame, None]:
        if target_frame < 0:
            return None

        if target_frame < len(self.state_cache):
            return self.state_cache[target_frame]

        for frame in range(len(self.state_cache) - 1, target_frame):
            new_entities: list[Entity] = []

            for entity in self.state_cache[frame].entities:
                new_entities.append(entity.deep_copy())

            # track gravity + entity momentum
            for entity in new_entities:
                entity.process_initial_step(self.gravity_scale * self.gravity_vector)

            for _ in range(ITERATIONS):
                for entity in new_entities:
                    # entity bones
                    entity.process_structural_bones()

                for entity in new_entities:
                    # entity-line collisions
                    entity.process_collisions(self.grid)

            # scarf bones
            for entity in new_entities:
                entity.process_flutter_bones()

            # dismount or sled break
            for entity in new_entities:
                entity.process_bind_triggers()

            self.state_cache.append(CachedFrame(new_entities))

        return self.state_cache[target_frame]

    # Primitive add and remove line methods
    # A proper implementation would look through the grid to optimize cache clears
    def add_line(self, line: PhysicsLine):
        line.id = self.grid.get_max_line_id() + 1
        self.state_cache = [self.state_cache[0]]
        self.grid.add_line(line)

    def remove_line(self, id: int):
        line = self.grid.get_line_by_id(id)
        if line != None:
            self.state_cache = [self.state_cache[0]]
            self.grid.remove_line(line)
