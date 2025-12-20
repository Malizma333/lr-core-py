from engine.vector import Vector
from engine.entity import Entity
from engine.grid import Grid, GridVersion
from engine.line import NormalLine, AccelerationLine
from engine.flags import GRAVITY_FIX
from typing import Optional, Union
import utils.debug


class CachedFrame:
    def __init__(self, entities: list[Entity]):
        self.entities: list[Entity] = entities


# Not specific implementation, just used for caching
class Engine:
    def __init__(
        self,
        grid_version: GridVersion,
        entities: list[Entity],
        lines: list[Union[NormalLine, AccelerationLine]],
    ):
        DEFAULT_CELL_SIZE = 14
        self.grid = Grid(grid_version, DEFAULT_CELL_SIZE)
        self.gravity_vector = Vector(0, 1)
        self.state_cache: list[CachedFrame] = [CachedFrame(entities)]

        self.gravity_scale = 0.175
        if GRAVITY_FIX:
            self.gravity_scale = 0.17500000000000002

        for line in lines:
            self.grid.add_line(line)

    def get_frame(self, target_frame: int) -> Optional[CachedFrame]:
        if target_frame < 0:
            return None

        gravity = self.gravity_scale * self.gravity_vector

        for frame in range(len(self.state_cache), target_frame + 1):
            new_entities: list[Entity] = []

            for entity in self.state_cache[frame - 1].entities:
                new_entities.append(entity.copy())

            for entity in new_entities:
                if utils.debug.at_breakpoint(None):
                    break
                # physics steps
                entity.process_skeleton(gravity, self.grid)

            for entity in new_entities:
                if utils.debug.at_breakpoint(None):
                    break
                # remount steps
                entity.process_remount(new_entities)

            self.state_cache.append(CachedFrame(new_entities))

        return self.state_cache[target_frame]

    # Primitive add and remove line methods
    # A proper implementation would look through the grid to optimize cache clears
    def add_line(self, line: Union[NormalLine, AccelerationLine]):
        line.base.id = self.grid.get_max_line_id() + 1
        self.state_cache = [self.state_cache[0]]
        self.grid.add_line(line)

    def remove_line(self, id: int):
        line = self.grid.get_line_by_id(id)
        if line != None:
            self.state_cache = [self.state_cache[0]]
            self.grid.remove_line(line)
