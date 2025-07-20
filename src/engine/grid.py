from engine.vector import Vector
from engine.line import PhysicsLine, LINE_HITBOX_HEIGHT
from engine.contact_point import ContactPoint
from enum import Enum
from typing import TypedDict
import math


class CellPosition(TypedDict):
    X: int
    Y: int
    REMAINDER_X: float
    REMAINDER_Y: float


class GridVersion(Enum):
    V6_2 = 0
    V6_1 = 1
    V6_0 = 2
    V6_7 = 3


# A container for lines that serves as an ordered list (descending line id order)
class GridCell:
    def __init__(self, position: CellPosition):
        self.lines: list[PhysicsLine] = []
        self.ids = set()
        self.position = position

    def add_line(self, new_line: PhysicsLine):
        for i, line in enumerate(self.lines):
            if line.id > new_line.id:
                self.lines.insert(i, new_line)
                self.ids.add(new_line.id)
                return

        self.lines.append(new_line)
        self.ids.add(new_line.id)

    def remove_line(self, line_id: int):
        for i, line in enumerate(self.lines):
            if line.id == line_id:
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
            line.endpoints[0], line.endpoints[1]
        ):
            self.register(line, position)

    def remove_line(self, line: PhysicsLine):
        for position in self.get_cell_positions_between(
            line.endpoints[0], line.endpoints[1]
        ):
            self.unregister(line, position)

    def move_line(self, line: PhysicsLine, old_pos1: Vector, old_pos2: Vector):
        for position in self.get_cell_positions_between(old_pos1, old_pos2):
            self.unregister(line, position)
        for position in self.get_cell_positions_between(
            line.endpoints[0], line.endpoints[1]
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
            self.cells[cell_key].remove_line(line.id)

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
        x = math.floor(position.x / self.cell_size)
        y = math.floor(position.y / self.cell_size)

        return {
            "X": x,
            "Y": y,
            "REMAINDER_X": position.x - x * self.cell_size,
            "REMAINDER_Y": position.y - y * self.cell_size,
        }

    def get_step_to_boundary(
        self,
        stepping_forwards: bool,
        cell_pos_component: float,
        cell_remainder_component: float,
    ) -> float:
        if cell_pos_component < 0:
            if stepping_forwards:
                return self.cell_size + cell_remainder_component
            else:
                return -(self.cell_size + cell_remainder_component)
        else:
            if stepping_forwards:
                return self.cell_size - cell_remainder_component
            else:
                return -1 - cell_remainder_component

    def get_step(self, line_vector: Vector, cell_pos: CellPosition) -> Vector:
        delta_x = self.get_step_to_boundary(
            line_vector.x > 0,
            cell_pos["X"],
            cell_pos["REMAINDER_X"],
        )
        delta_y = self.get_step_to_boundary(
            line_vector.y > 0,
            cell_pos["Y"],
            cell_pos["REMAINDER_Y"],
        )

        if line_vector.x == 0:
            step = Vector(0, delta_y)
        elif line_vector.y == 0:
            step = Vector(delta_x, 0)
        else:
            step = Vector(
                delta_y * line_vector.x / line_vector.y,
                delta_x * line_vector.y / line_vector.x,
            )
            if abs(step.y) <= abs(delta_y):
                step.x = delta_x
            else:
                step.y = delta_y

        return step

    def get_cell_positions_between(
        self, pos1: Vector, pos2: Vector
    ) -> list[CellPosition]:
        initial_cell = self.get_cell_position(pos1)
        final_cell = self.get_cell_position(pos2)
        cells = []

        if (
            initial_cell["X"] == final_cell["X"]
            and initial_cell["Y"] == final_cell["Y"]
        ):
            return [initial_cell]

        lower_bound_x = min(initial_cell["X"], final_cell["X"])
        lower_bound_y = min(initial_cell["Y"], final_cell["Y"])
        upper_bound_x = max(initial_cell["X"], final_cell["X"])
        upper_bound_y = max(initial_cell["Y"], final_cell["Y"])

        current_position = pos1.copy()
        curr_cell_pos = initial_cell

        if self.version == GridVersion.V6_2 or self.version == GridVersion.V6_7:
            while (
                lower_bound_x <= curr_cell_pos["X"]
                and curr_cell_pos["X"] <= upper_bound_x
                and lower_bound_y <= curr_cell_pos["Y"]
                and curr_cell_pos["Y"] <= upper_bound_y
            ):
                cells.append(curr_cell_pos)
                current_position += self.get_step(pos2 - pos1, curr_cell_pos)
                next_cell_pos = self.get_cell_position(current_position)

                # Avoid 6.1 grid bug (TODO merge in?)
                if (
                    next_cell_pos["X"] == curr_cell_pos["X"]
                    and next_cell_pos["Y"] == curr_cell_pos["Y"]
                ):
                    break

                curr_cell_pos = next_cell_pos
        else:
            pass
        return cells

    def get_interacting_lines(self, point: ContactPoint):
        involved_lines: list[PhysicsLine] = []
        # get cells in a 3 x 3, but more if line_hitbox_height >= grid_cell_size
        bounds_size = math.floor(1 + LINE_HITBOX_HEIGHT / self.cell_size)
        for x_offset in range(-bounds_size, bounds_size + 1):
            for y_offset in range(-bounds_size, bounds_size + 1):
                cell = self.get_cell(
                    point.position + self.cell_size * Vector(x_offset, y_offset)
                )

                if cell != None:
                    for line in cell.lines:
                        # Intentionally contains duplicates, ordered by id
                        involved_lines.append(line)

        return involved_lines
