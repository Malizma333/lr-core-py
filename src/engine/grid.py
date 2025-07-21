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
            if line.id < new_line.id:
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

    def get_next_pos_v62(
        self,
        curr_pos: Vector,
        curr_cell_pos: CellPosition,
        line_point_1: Vector,
        line_point_2: Vector,
    ) -> Vector:
        line_vector = line_point_2 - line_point_1

        if line_vector.x > 0:
            delta_x = self.cell_size - curr_cell_pos["REMAINDER_X"]
        else:
            delta_x = -1 - curr_cell_pos["REMAINDER_X"]

        if line_vector.y > 0:
            delta_y = self.cell_size - curr_cell_pos["REMAINDER_Y"]
        else:
            delta_y = -1 - curr_cell_pos["REMAINDER_Y"]

        # Adds correction for negative cell positions
        if curr_cell_pos["X"] < 0:
            if line_vector.x > 0:
                delta_x = self.cell_size + curr_cell_pos["REMAINDER_X"]
            else:
                delta_x = -(self.cell_size + curr_cell_pos["REMAINDER_X"])

        if curr_cell_pos["Y"] < 0:
            if line_vector.y > 0:
                delta_y = self.cell_size + curr_cell_pos["REMAINDER_X"]
            else:
                delta_y = -(self.cell_size + curr_cell_pos["REMAINDER_Y"])

        if line_vector.x == 0:
            next_pos = Vector(curr_pos.x, curr_pos.y + delta_y)
        elif line_vector.y == 0:
            next_pos = Vector(curr_pos.x + delta_x, curr_pos.y)
        else:
            # Uses a different slope algorithm for getting next position
            y_based_delta_x = delta_y * line_vector.x / line_vector.y
            x_based_delta_y = delta_x * line_vector.y / line_vector.x
            next_x = curr_pos.x + y_based_delta_x
            next_y = curr_pos.y + x_based_delta_y
            if abs(x_based_delta_y) < abs(delta_y):
                next_pos = Vector(curr_pos.x + delta_x, next_y)
            elif abs(x_based_delta_y) == abs(delta_y):
                next_pos = Vector(curr_pos.x + delta_x, curr_pos.y + delta_y)
            else:
                next_pos = Vector(next_x, curr_pos.y + delta_y)

        return next_pos

    def get_next_pos_v61(
        self,
        curr_pos: Vector,
        curr_cell_pos: CellPosition,
        line_point_1: Vector,
        line_point_2: Vector,
    ) -> Vector:
        line_vector = line_point_2 - line_point_1

        if line_vector.x != 0 and line_vector.y != 0:
            slope = line_vector.y / line_vector.x
        else:
            slope = 0

        if line_vector.x > 0:
            delta_x = self.cell_size - curr_cell_pos["REMAINDER_X"]
        else:
            delta_x = -1 - curr_cell_pos["REMAINDER_X"]

        if line_vector.y > 0:
            delta_y = self.cell_size - curr_cell_pos["REMAINDER_Y"]
        else:
            delta_y = -1 - curr_cell_pos["REMAINDER_Y"]

        if line_vector.x == 0:
            next_pos = Vector(curr_pos.x, curr_pos.x + delta_y)
        elif line_vector.y == 0:
            next_pos = Vector(delta_x + curr_pos.x, curr_pos.y)
        else:
            y_intercept = line_point_1.y - slope * line_point_1.x
            next_x = round((curr_pos.y + delta_y - y_intercept) / slope)
            next_y = round(slope * (curr_pos.x + delta_x) + y_intercept)
            if abs(next_y - curr_pos.y) < abs(delta_y):
                next_pos = Vector(curr_pos.x + delta_x, next_y)
            elif abs(next_y - curr_pos.y) == abs(delta_y):
                next_pos = Vector(curr_pos.x + delta_x, curr_pos.y + delta_y)
            else:
                next_pos = Vector(next_x, curr_pos.y + delta_y)

        return next_pos

    def get_cell_positions_between(
        self, line_pos1: Vector, line_pos2: Vector
    ) -> list[CellPosition]:
        cells = []
        initial_cell = self.get_cell_position(line_pos1)
        final_cell = self.get_cell_position(line_pos2)

        if line_pos1 == line_pos2 or (
            initial_cell["X"] == final_cell["X"]
            and initial_cell["Y"] == final_cell["Y"]
        ):
            return [initial_cell]

        lower_bound_x = min(initial_cell["X"], final_cell["X"])
        lower_bound_y = min(initial_cell["Y"], final_cell["Y"])
        upper_bound_x = max(initial_cell["X"], final_cell["X"])
        upper_bound_y = max(initial_cell["Y"], final_cell["Y"])

        current_position = line_pos1.copy()
        curr_cell_pos = initial_cell

        while (
            lower_bound_x <= curr_cell_pos["X"]
            and curr_cell_pos["X"] <= upper_bound_x
            and lower_bound_y <= curr_cell_pos["Y"]
            and curr_cell_pos["Y"] <= upper_bound_y
        ):
            cells.append(curr_cell_pos)

            if self.version == GridVersion.V6_0:
                break  # TODO
            elif self.version == GridVersion.V6_1:
                current_position = self.get_next_pos_v61(
                    current_position, curr_cell_pos, line_pos1, line_pos2
                )
            else:
                current_position = self.get_next_pos_v62(
                    current_position, curr_cell_pos, line_pos1, line_pos2
                )

            next_cell_pos = self.get_cell_position(current_position)

            # Avoid 6.1 grid bug
            if (
                next_cell_pos["X"] == curr_cell_pos["X"]
                and next_cell_pos["Y"] == curr_cell_pos["Y"]
            ):
                break

            curr_cell_pos = next_cell_pos

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
