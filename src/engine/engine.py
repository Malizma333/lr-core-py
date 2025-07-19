from typing import Union, TypedDict
from engine.vector import Vector
from engine.entity import Entity, ContactPoint
from engine.grid import Grid, GridCell, GridVersion


class PhysicsLine(TypedDict):
    ID: int
    ENDPOINTS: tuple[Vector, Vector]
    FLIPPED: bool
    LEFT_EXTENSION: bool
    RIGHT_EXTENSION: bool
    MULTIPLIER: float  # zero for blue lines, otherwise red line


ACCELERATION_MULT = 0.1
FRAMES_PER_SECOND = 40
NUM_ITERATIONS = 6
LINE_HITBOX_HEIGHT = 10
GRID_CELL_SIZE = 14
MAX_LINE_EXTENSION_RATIO = 0.25
GRAVITY = Vector(0, 1)
GRAVITY_SCALE = 0.175
GRAVITY_SCALE_V6_7 = 0.17500000000000002  # Just one bit off :(


def interact_with_line(point: ContactPoint, line: PhysicsLine):
    line_vector = line["ENDPOINTS"][1] - line["ENDPOINTS"][0]
    line_magnitude = line_vector.magnitude()
    unit_line_vector = line_vector / line_magnitude

    line_normal_vector = unit_line_vector.rot_ccw()
    if line["FLIPPED"]:
        line_normal_vector = unit_line_vector.rot_cw()

    ext_ratio = min(MAX_LINE_EXTENSION_RATIO, LINE_HITBOX_HEIGHT / line_magnitude)

    limit_left = 0.0
    if line["LEFT_EXTENSION"]:
        limit_left -= ext_ratio

    limit_right = 1.0
    if line["RIGHT_EXTENSION"]:
        limit_right += ext_ratio

    accel = line_normal_vector * ACCELERATION_MULT * line["MULTIPLIER"]

    # TODO suspicious of this
    accel = accel.rot_ccw()
    if line["FLIPPED"]:
        accel = accel.rot_cw()

    if not ((point["velocity"] @ line_normal_vector) > 0):
        return False

    line_endpoint_to_contact_point = point["position"] - line["ENDPOINTS"][0]
    dist_from_line_top = line_normal_vector @ line_endpoint_to_contact_point

    if not (0 < dist_from_line_top and dist_from_line_top < LINE_HITBOX_HEIGHT):
        return False

    pos_between_ends = (
        line_endpoint_to_contact_point @ line_vector
    ) / line_magnitude**2

    if not (limit_left <= pos_between_ends and pos_between_ends <= limit_right):
        return False

    new_position = point["position"] - dist_from_line_top * line_normal_vector
    previous_position = point["position"] - point["velocity"]
    friction_vector = line_normal_vector * point["FRICTION"] * dist_from_line_top

    if previous_position.x >= new_position.x:
        friction_vector.x = -friction_vector.x
    if previous_position.y >= new_position.y:
        friction_vector.y = -friction_vector.y

    # TODO this might be wrong (StandardLine.Interact + RedLine.Interact)
    # Side effects
    point["position"] = new_position
    point["velocity"] = point["position"] - (
        previous_position + friction_vector + accel
    )

    return True


# Not specific implementation, just used for caching
class Engine:
    def __init__(
        self,
        grid_version: GridVersion,
        riders: list[Entity],
        lines: list[PhysicsLine],
    ):
        self.grid = Grid(grid_version, GRID_CELL_SIZE)
        self.gravity_scale = GRAVITY_SCALE
        self.state_cache: list[list[Entity]] = [[]]
        self.riders = riders

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
                # gravity
                for point_index in range(len(entity.points)):
                    new_entities[entity_index].points[point_index]["velocity"] += (
                        GRAVITY * self.gravity_scale
                    )

                # momentum
                for point_index, point in enumerate(entity.points):
                    new_entities[entity_index].points[point_index]["position"] += point[
                        "velocity"
                    ]

                for _ in range(NUM_ITERATIONS):
                    # bones
                    entity.process_bones()

                    # line collisions
                    for point_index, point in enumerate(entity.points):
                        position = point["position"]
                        involved_cells: list[GridCell] = []

                        # get cells in a 3 x 3, but more if line_hitbox_height >= grid_cell_size
                        bounds_size = int(1 + LINE_HITBOX_HEIGHT / self.grid.cell_size)
                        for x_offset in range(-bounds_size, bounds_size + 1):
                            for y_offset in range(-bounds_size, bounds_size + 1):
                                cell = self.grid.get_cell(
                                    position
                                    + self.grid.cell_size * Vector(x_offset, y_offset)
                                )

                                if cell != None:
                                    involved_cells.append(cell)

                        # collide with involved cells
                        for cell in involved_cells:
                            for line in cell.lines:
                                _collision_occurred = interact_with_line(point, line)

            self.state_cache.append(new_entities)

        return self.state_cache[target_frame]
