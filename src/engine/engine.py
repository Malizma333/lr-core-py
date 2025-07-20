from typing import Union
from engine.vector import Vector
from engine.entity import Entity
from engine.grid import Grid, GridVersion
from engine.line import PhysicsLine


GRID_CELL_SIZE = 14
FRAMES_PER_SECOND = 40
NUM_ITERATIONS = 6
GRAVITY = Vector(0, 1)
GRAVITY_SCALE = 0.175
GRAVITY_SCALE_V6_7 = 0.17500000000000002  # Just one bit off :(


# Not specific implementation, just used for caching
class Engine:
    def __init__(
        self,
        grid_version: GridVersion,
        entities: list[Entity],
        lines: list[PhysicsLine],
    ):
        self.grid = Grid(grid_version, GRID_CELL_SIZE)
        self.gravity_scale = GRAVITY_SCALE
        self.state_cache: list[list[Entity]] = [[entity.copy() for entity in entities]]

        if grid_version == GridVersion.V6_7:
            self.gravity_scale = GRAVITY_SCALE_V6_7

        for line in lines:
            self.grid.add_line(line)

    # TODO: Support adding and removing lines, refreshing physics cache

    def get_frame(self, target_frame: int) -> Union[list[Entity], None]:
        if target_frame < 0:
            return None

        if target_frame < len(self.state_cache):
            return self.state_cache[target_frame]

        for frame in range(len(self.state_cache) - 1, target_frame):
            new_entities: list[Entity] = []

            for entity in self.state_cache[frame]:
                new_entities.append(entity.copy())

            for entity_index, entity in enumerate(new_entities):
                # gravity + momentum

                for point_index, point in enumerate(entity.points):
                    new_velocity = (
                        point.position
                        - point.previous_position
                        + (self.gravity_scale * GRAVITY)
                    )
                    current_position = point.position.copy()
                    new_entities[entity_index].points[point_index].set_velocity(
                        new_velocity
                    )
                    new_entities[entity_index].points[point_index].set_prev_position(
                        current_position
                    )
                    new_entities[entity_index].points[point_index].set_position(
                        current_position + new_velocity
                    )

                for _ in range(NUM_ITERATIONS):
                    # bones
                    for _bone_index, bone in enumerate(entity.bones):
                        entity.process_bone(bone)

                    # point-line collisions
                    for point_index, point in enumerate(entity.points):
                        for line in self.grid.get_interacting_lines(point):
                            line.interact(point)

            # TODO death check

            self.state_cache.append(new_entities)

        return self.state_cache[target_frame]
