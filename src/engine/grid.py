from engine.vector import Vector
from engine.line import PhysicsLine, LINE_HITBOX_HEIGHT
from engine.entity import ContactPoint
from enum import Enum
from typing import TypedDict


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


# A container for lines that serves as an ordered list
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

    def get_interacting_lines(self, point: ContactPoint):
        involved_lines: list[PhysicsLine] = []
        # get cells in a 3 x 3, but more if line_hitbox_height >= grid_cell_size
        bounds_size = int(1 + LINE_HITBOX_HEIGHT / self.cell_size)
        for x_offset in range(-bounds_size, bounds_size + 1):
            for y_offset in range(-bounds_size, bounds_size + 1):
                cell = self.get_cell(
                    point.position + self.cell_size * Vector(x_offset, y_offset)
                )

                if cell != None:
                    for line in cell.lines:
                        involved_lines.append(line)
        return involved_lines
