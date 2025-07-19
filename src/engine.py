# The physics engine

from typing import Union
from lrtypes import (
    InitialEntityParams,
    PhysicsLine,
    EntityState,
    Entity,
    GridVersion,
    NormalBone,
    MountBone,
    RepelBone,
    ContactPoint,
    CellPosition,
)
from vector import Vector

ACCELERATION_MULT = 0.1
FRAMES_PER_SECOND = 40
NUM_ITERATIONS = 6
LINE_HITBOX_HEIGHT = 10
GRID_CELL_SIZE = 14
MAX_LINE_EXTENSION_RATIO = 0.25
GRAVITY = Vector(0, 1)
GRAVITY_SCALE = 0.175
GRAVITY_SCALE_V6_7 = 0.17500000000000002  # Just one bit off :(
BONE_ENDURANCE = 0.0285

# TODO remove side effects from functions
# TODO remount physics? + remount versions (lra vs .com)?
# TODO scarf physics? + scarf versions (lra vs .com)?


def make_rider(startState: InitialEntityParams) -> Entity:
    entity: Entity = {"bones": [], "points": [], "state": EntityState.MOUNTED}

    POINT_DATA = [
        (Vector(10.0, 5.0), 0.0),  # left foot
        (Vector(10.0, 5.0), 0.0),  # right foot
        (Vector(11.5, -5.0), 0.1),  # left hand
        (Vector(11.5, -5.0), 0.1),  # right hand
        (Vector(5.0, -5.5), 0.8),  # shoulder
        (Vector(5.0, 0.0), 0.8),  # butt
        (Vector(0.0, 0.0), 0.8),  # peg
        (Vector(15.0, 5.0), 0.0),  # nose
        (Vector(0.0, 5.0), 0.0),  # tail
        (Vector(17.5, 0.0), 0.0),  # string
    ]

    BONE_DATA = [
        ("NORMAL", 6, 8, 0.0),  # peg-tail
        ("NORMAL", 8, 7, 0.0),  # tail-nose
        ("NORMAL", 7, 9, 0.0),  # nose-string
        ("NORMAL", 9, 6, 0.0),  # string-peg
        ("MOUNT", 6, 5, 0.057),  # peg-butt
        ("MOUNT", 8, 5, 0.057),  # tail-butt
        ("MOUNT", 7, 5, 0.057),  # nose-butt
        ("NORMAL", 4, 5, 0.0),  # shoulder-butt
        ("NORMAL", 4, 2, 0.0),  # shoulder-lefthand
        ("NORMAL", 4, 3, 0.0),  # shoulder-righthand
        ("NORMAL", 5, 0, 0.0),  # butt-leftfoot
        ("NORMAL", 5, 1, 0.0),  # butt-rightfoot
        ("MOUNT", 4, 6, 0.057),  # shoulder-peg
        ("MOUNT", 9, 2, 0.057),  # string-lefthand
        ("MOUNT", 9, 3, 0.057),  # string-righthand
        ("MOUNT", 0, 7, 0.057),  # leftfoot-nose
        ("MOUNT", 1, 7, 0.057),  # rightfoot-nose
        ("REPEL", 4, 0, 0.5),  # shoulder-leftfoot
        ("REPEL", 4, 1, 0.5),  # shoulder-rightfoot
    ]

    for init_pos, friction in POINT_DATA:
        entity["points"].append(
            {
                "position": init_pos + startState["POSITION"],
                "velocity": Vector(0, 0) + startState["VELOCITY"],
                "FRICTION": friction,
            }
        )

    for bone_tuple in BONE_DATA:
        bone_type = bone_tuple[0]
        point1_index = bone_tuple[1]
        point2_index = bone_tuple[2]
        cp1 = entity["points"][point1_index]
        cp2 = entity["points"][point2_index]
        rest_length = cp1["position"].distance_from(cp2["position"])

        if bone_type == "NORMAL":
            normal_bone: NormalBone = {
                "POINT1": point1_index,
                "POINT2": point2_index,
                "RESTING_LENGTH": rest_length,
            }
            entity["bones"].append(normal_bone)
        elif bone_type == "MOUNT":
            mount_bone: MountBone = {
                "POINT1": point1_index,
                "POINT2": point2_index,
                "RESTING_LENGTH": rest_length,
                "ENDURANCE": bone_tuple[3],
            }
            entity["bones"].append(mount_bone)
        else:
            repel_bone: RepelBone = {
                "POINT1": point1_index,
                "POINT2": point2_index,
                "RESTING_LENGTH": rest_length,
                "LENGTH_FACTOR": bone_tuple[3],
            }
            entity["bones"].append(repel_bone)

    return entity


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

    # Side effects
    # TODO this might be wrong (StandardLine.Interact + RedLine.Interact)
    point["position"] = new_position
    point["velocity"] = point["position"] - (
        previous_position + friction_vector + accel
    )

    return True


def simulate_bone(
    bone: Union[NormalBone, MountBone, RepelBone],
    entity: Entity,
    entities: list[Entity],
    entity_index: int,
):
    joint1 = bone["POINT1"]
    joint2 = bone["POINT2"]
    position1 = entity["points"][joint1]["position"]
    position2 = entity["points"][joint2]["position"]
    delta = position1 - position2
    magnitude = delta.magnitude()
    rest_length = bone["RESTING_LENGTH"]

    if type(bone) == RepelBone:
        rest_length *= bone["LENGTH_FACTOR"]

    if type(bone) != RepelBone or magnitude < rest_length:
        if magnitude * 0.5 != 0:
            scalar = (magnitude - rest_length) / magnitude * 0.5
        else:
            scalar = 0

        # Side effects
        if type(bone) == MountBone and (
            entity["state"] == EntityState.DISMOUNTED
            or scalar > rest_length * BONE_ENDURANCE
        ):
            entities[entity_index]["state"] = EntityState.DISMOUNTED
        else:
            entities[entity_index]["points"][joint1]["position"] -= delta * scalar
            entities[entity_index]["points"][joint2]["position"] += delta * scalar


# A container for lines that serves as an ordered list
class GridCell:
    def __init__(self, position: CellPosition):
        self.lines: list[PhysicsLine] = []
        self.ids = set()
        self.position = position

    def add_line(self, new_line: PhysicsLine):
        for i, line in enumerate(self.lines):
            if line["ID"] < new_line["ID"]:
                self.lines.insert(i, new_line)
                self.ids.add(new_line["ID"])
                return

        self.lines.append(new_line)
        self.ids.add(new_line["ID"])

    def remove_line(self, line_id: int):
        for i, line in enumerate(self.lines):
            if line["ID"] == line_id:
                del self.lines[i]
                self.ids.remove(line_id)
                return


# TODO 6.1
# TODO 6.0?


# A grid of GridCells that processes all of the lines
class Grid:
    def __init__(self, version: GridVersion, cell_size: float):
        self.version = version
        self.cells: dict[int, GridCell] = {}
        self.cell_size = cell_size

    def add_line(self, line: PhysicsLine):
        for position in self.get_cell_positions_between(
            line["ENDPOINTS"][0], line["ENDPOINTS"][1]
        ):
            self.register(line, position)

    def remove_line(self, line: PhysicsLine):
        for position in self.get_cell_positions_between(
            line["ENDPOINTS"][0], line["ENDPOINTS"][1]
        ):
            self.unregister(line, position)

    def move_line(self, line: PhysicsLine, old_pos1: Vector, old_pos2: Vector):
        for position in self.get_cell_positions_between(old_pos1, old_pos2):
            self.unregister(line, position)
        for position in self.get_cell_positions_between(
            line["ENDPOINTS"][0], line["ENDPOINTS"][1]
        ):
            self.register(line, position)

    def register(self, line: PhysicsLine, position: CellPosition):
        cell_key = self.hash_int_pair(position["X"], position["Y"])
        if cell_key not in self.cells:
            self.cells[cell_key] = GridCell(position.copy())
        self.cells[cell_key].add_line(line)

    def unregister(self, line: PhysicsLine, position: CellPosition):
        cell_key = self.hash_int_pair(position["X"], position["Y"])
        if cell_key in self.cells:
            self.cells[cell_key].remove_line(line["ID"])

    # No specific implementation, just needs to be deterministic
    def hash_int_pair(self, x: int, y: int) -> int:
        return (x * 73856093) ^ (y * 19349663)

    def get_cell(self, position: Vector):
        cell_position = self.get_cell_position(position)
        cell_key = self.hash_int_pair(cell_position["X"], cell_position["Y"])
        if cell_key in self.cells:
            return self.cells[cell_key]
        return None

    def get_cell_position(self, position: Vector) -> CellPosition:
        x = int(position.x / self.cell_size)
        y = int(position.y / self.cell_size)

        return {
            "X": x,
            "Y": y,
            "REMAINDER_X": position.x - x * self.cell_size,
            "REMAINDER_Y": position.y - y * self.cell_size,
        }

    def get_step(self, forwards: bool, cellpos: float, remainder: float):
        if forwards:
            if cellpos < 0:
                return self.cell_size + remainder
            else:
                return self.cell_size - remainder
        else:
            if cellpos < 0:
                return -(self.cell_size + remainder)
            else:
                return -(remainder + 1)

    def get_cell_positions_between(
        self, pos1: Vector, pos2: Vector
    ) -> list[CellPosition]:
        delta = pos2 - pos1
        initial_cell = self.get_cell_position(pos1)
        final_cell = self.get_cell_position(pos2)

        cells = [initial_cell]

        if (
            initial_cell["X"] == final_cell["X"]
            and initial_cell["Y"] == final_cell["Y"]
        ):
            return cells

        lower_bound = (
            min(initial_cell["X"], final_cell["X"]),
            min(initial_cell["Y"], final_cell["Y"]),
        )

        upper_bound = (
            max(initial_cell["X"], final_cell["X"]),
            max(initial_cell["Y"], final_cell["Y"]),
        )

        current_position = pos1.copy()
        current_cell = initial_cell
        x_forwards = delta.x > 0
        y_forwards = delta.y > 0

        if self.version == GridVersion.V6_2 or self.version == GridVersion.V6_7:
            while True:
                boundary_x = self.get_step(
                    x_forwards, current_cell["X"], current_cell["REMAINDER_X"]
                )
                boundary_y = self.get_step(
                    y_forwards, current_cell["Y"], current_cell["REMAINDER_Y"]
                )
                step = Vector(
                    boundary_y * delta.x / delta.y, boundary_x * delta.y / delta.x
                )

                if abs(step.x) > abs(boundary_x):
                    step.x = boundary_x

                if abs(step.y) > abs(boundary_y):
                    step.y = boundary_y

                current_position += step
                current_cell = self.get_cell_position(current_position)

                if not (
                    lower_bound[0] <= current_cell["X"]
                    and current_cell["X"] <= upper_bound[0]
                    and lower_bound[1] <= current_cell["Y"]
                    and current_cell["Y"] <= upper_bound[1]
                ):
                    return cells

                cells.append(current_cell)
        else:
            pass

        return cells


def get_frame(
    grid_version: GridVersion,
    target_frame: int,
    riders: list[InitialEntityParams],
    lines: list[PhysicsLine],
) -> Union[list[Entity], None]:
    if target_frame < 0:
        return None

    gravity_scale = GRAVITY_SCALE
    if grid_version == GridVersion.V6_7:
        gravity_scale = GRAVITY_SCALE_V6_7

    entities: list[Entity] = []
    grid = Grid(grid_version, GRID_CELL_SIZE)

    for line in lines:
        grid.add_line(line)

    for initial_rider_state in riders:
        entities.append(make_rider(initial_rider_state))

    for frame in range(target_frame):
        for entity_index, entity in enumerate(entities):
            # gravity
            for point_index in range(len(entity["points"])):
                entities[entity_index]["points"][point_index]["velocity"] += (
                    GRAVITY * gravity_scale
                )

            # momentum
            for point_index, point in enumerate(entity["points"]):
                entities[entity_index]["points"][point_index]["position"] += point[
                    "velocity"
                ]

            for _ in range(NUM_ITERATIONS):
                # bones
                for bone in entity["bones"]:
                    simulate_bone(bone, entity, entities, entity_index)

                # line collisions
                for point_index, point in enumerate(entity["points"]):
                    position = point["position"]
                    involved_cells: list[GridCell] = []

                    # get cells in a 3 x 3, but more if line_hitbox_height >= grid_cell_size
                    bounds_size = int(1 + LINE_HITBOX_HEIGHT / grid.cell_size)
                    for x_offset in range(-bounds_size, bounds_size + 1):
                        for y_offset in range(-bounds_size, bounds_size + 1):
                            cell = grid.get_cell(
                                position + grid.cell_size * Vector(x_offset, y_offset)
                            )

                            if cell != None:
                                involved_cells.append(cell)

                    # collide with involved cells
                    for cell in involved_cells:
                        for line in cell.lines:
                            _collision_occurred = interact_with_line(point, line)

    return entities
