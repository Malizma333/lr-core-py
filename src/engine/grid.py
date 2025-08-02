from engine.vector import Vector
from engine.line import Line
from engine.point import ContactPoint
from enum import Enum
from typing import Union
import math


class GridVersion(Enum):
    V6_2 = 0
    V6_1 = 1
    V6_0 = 2
    V6_3 = 3
    V6_7 = 4


class CellPosition:
    def __init__(self, world_position: Vector, cell_size: int):
        self.cell_size = cell_size
        self.world_position = world_position.copy()
        self.x = math.floor(world_position.x / cell_size)
        self.y = math.floor(world_position.y / cell_size)
        self.remainder = self.world_position - cell_size * Vector(self.x, self.y)

    # No specific implementation, just needs to be deterministic
    def get_key(self) -> int:
        return (self.x * 73856093) ^ (self.y * 19349663)


# A container for lines that serves as an ordered list (descending line id order)
class GridCell:
    def __init__(self, position: CellPosition):
        self.lines: list[Line] = []
        self.ids = set()
        self.position = position

    def add_line(self, new_line: Line):
        for i, line in enumerate(self.lines):
            if line.base.id < new_line.base.id:
                self.lines.insert(i, new_line)
                self.ids.add(new_line.base.id)
                return

        self.lines.append(new_line)
        self.ids.add(new_line.base.id)

    def remove_line(self, line_id: int):
        for i, line in enumerate(self.lines):
            if line.base.id == line_id:
                del self.lines[i]
                self.ids.remove(line_id)
                return


# A grid of GridCells that processes all of the lines
class Grid:
    def __init__(self, version: GridVersion, cell_size: int):
        self.version = version
        self.cells: dict[int, GridCell] = {}
        self.cell_size = cell_size

    def get_max_line_id(self) -> int:
        max_found = -1
        if self.cells:
            for cell in self.cells.values():
                if cell.lines:
                    for line in cell.lines:
                        if line.base.id > max_found:
                            max_found = line.base.id
        return max_found

    def get_line_by_id(self, line_id: int) -> Union[Line, None]:
        for cell in self.cells.values():
            if line_id in cell.ids:
                for line in cell.lines:
                    if line.base.id == line_id:
                        return line
        return None

    def add_line(self, line: Line):
        for position in self.get_cell_positions_between(
            line.base.endpoints[0], line.base.endpoints[1]
        ):
            self.register(line, position)

    def remove_line(self, line: Line):
        for position in self.get_cell_positions_between(
            line.base.endpoints[0], line.base.endpoints[1]
        ):
            self.unregister(line, position)

    def move_line(self, old_point1: Vector, old_point2: Vector, line: Line):
        for position in self.get_cell_positions_between(old_point1, old_point2):
            self.unregister(line, position)

        for position in self.get_cell_positions_between(
            line.base.endpoints[0], line.base.endpoints[1]
        ):
            self.register(line, position)

    def register(self, line: Line, position: CellPosition):
        cell_key = position.get_key()
        if cell_key not in self.cells:
            self.cells[cell_key] = GridCell(
                self.get_cell_position(position.world_position)
            )
        self.cells[cell_key].add_line(line)

    def unregister(self, line: Line, position: CellPosition):
        cell_key = position.get_key()
        if cell_key in self.cells:
            self.cells[cell_key].remove_line(line.base.id)

    def get_cell(self, position: Vector):
        cell_position = self.get_cell_position(position)
        cell_key = cell_position.get_key()
        if cell_key in self.cells:
            return self.cells[cell_key]
        return None

    def get_cell_position(self, position: Vector) -> CellPosition:
        return CellPosition(position, self.cell_size)

    def get_next_position(
        self,
        curr_pos: Vector,
        curr_cell_pos: CellPosition,
        point1: Vector,
        point2: Vector,
    ) -> Vector:
        line_vector = point2 - point1

        if line_vector.x > 0:
            delta_x = self.cell_size - curr_cell_pos.remainder.x
        else:
            delta_x = -1 - curr_cell_pos.remainder.x

        if line_vector.y > 0:
            delta_y = self.cell_size - curr_cell_pos.remainder.y
        else:
            delta_y = -1 - curr_cell_pos.remainder.y

        if self.version == GridVersion.V6_2 or self.version == GridVersion.V6_7:
            # Add correction for negative cell positions
            if curr_cell_pos.x < 0:
                if line_vector.x > 0:
                    delta_x = self.cell_size + curr_cell_pos.remainder.x
                else:
                    delta_x = -(self.cell_size + curr_cell_pos.remainder.x)

            if curr_cell_pos.y < 0:
                if line_vector.y > 0:
                    delta_y = self.cell_size + curr_cell_pos.remainder.x
                else:
                    delta_y = -(self.cell_size + curr_cell_pos.remainder.x)

        if line_vector.x == 0:
            next_pos = Vector(curr_pos.x, curr_pos.y + delta_y)
        elif line_vector.y == 0:
            next_pos = Vector(curr_pos.x + delta_x, curr_pos.y)
        elif self.version == GridVersion.V6_1:
            slope = line_vector.y / line_vector.x
            y_intercept = point1.y - slope * point1.x
            next_x = round((curr_pos.y + delta_y - y_intercept) / slope)
            next_y = round(slope * (curr_pos.x + delta_x) + y_intercept)
            if abs(next_y - curr_pos.y) < abs(delta_y):
                next_pos = Vector(curr_pos.x + delta_x, next_y)
            elif abs(next_y - curr_pos.y) == abs(delta_y):
                next_pos = Vector(curr_pos.x + delta_x, curr_pos.y + delta_y)
            else:
                next_pos = Vector(next_x, curr_pos.y + delta_y)
        else:
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

    def get_cell_positions_between(
        self, point1: Vector, point2: Vector
    ) -> list[CellPosition]:
        cells = []
        initial_cell = self.get_cell_position(point1)
        final_cell = self.get_cell_position(point2)
        lower_bound_x = min(initial_cell.x, final_cell.x)
        lower_bound_y = min(initial_cell.y, final_cell.y)
        upper_bound_x = max(initial_cell.x, final_cell.x)
        upper_bound_y = max(initial_cell.y, final_cell.y)
        curr_pos = point1.copy()
        curr_cell_pos = initial_cell

        line_vector = point2 - point1
        line_normal_unit = line_vector.rot_ccw() * (1 / line_vector.length())

        if (point1.x == point2.x and point1.y == point2.y) or (
            initial_cell.x == final_cell.x and initial_cell.y == final_cell.y
        ):
            return [initial_cell]

        if (
            self.version == GridVersion.V6_0
            or self.version == GridVersion.V6_3
            or self.version == GridVersion.V6_7
        ):
            # Reference: https://github.com/kevansevans/OpenLR/blob/542bb76e85aff820ae720cfc0d5af1bb4eb50969/src/hxlr/engine/Grid.hx#L251
            line_halfway = 0.5 * Vector(abs(line_vector.x), abs(line_vector.y))
            line_midpoint = point1 + line_vector * 0.5
            absolute_normal = Vector(abs(line_normal_unit.x), abs(line_normal_unit.y))
            # Finds axis-aligned bounding box and filters it
            for cell_x in range(lower_bound_x, upper_bound_x + 1):
                for cell_y in range(lower_bound_y, upper_bound_y + 1):
                    # Note: The sign of line.normal_unit is not important here (cancelled out)
                    curr_pos = self.cell_size * Vector(cell_x + 0.5, cell_y + 0.5)
                    next_cell_pos = self.get_cell_position(curr_pos)
                    dist_between_centers = line_midpoint - curr_pos
                    dist_from_cell_center = absolute_normal @ next_cell_pos.remainder
                    cell_overlap_into_hitbox = (
                        Vector(dist_from_cell_center, dist_from_cell_center)
                        @ absolute_normal
                    )
                    norm_dist_between_centers = line_normal_unit @ dist_between_centers
                    dist_from_line = abs(
                        norm_dist_between_centers * line_normal_unit.x
                    ) + abs(norm_dist_between_centers * line_normal_unit.y)
                    if (
                        line_halfway.x + next_cell_pos.remainder.x
                        >= abs(dist_between_centers.x)
                        and line_halfway.y + next_cell_pos.remainder.y
                        >= abs(dist_between_centers.y)
                        and cell_overlap_into_hitbox >= dist_from_line
                    ):
                        cells.append(next_cell_pos)
        else:
            # Performs DDA stepping
            while (
                lower_bound_x <= curr_cell_pos.x
                and curr_cell_pos.x <= upper_bound_x
                and lower_bound_y <= curr_cell_pos.y
                and curr_cell_pos.y <= upper_bound_y
            ):
                cells.append(curr_cell_pos)
                curr_pos = self.get_next_position(
                    curr_pos, curr_cell_pos, point1, point2
                )
                next_cell_pos = self.get_cell_position(curr_pos)

                # This causes a crash in 6.1, so just break early
                if (
                    next_cell_pos.x == curr_cell_pos.x
                    and next_cell_pos.y == curr_cell_pos.y
                ):
                    break

                curr_cell_pos = next_cell_pos

        return cells

    def get_interacting_lines(self, point: ContactPoint):
        interacting_lines: list[Line] = []
        # Get cells in a 3 x 3
        # May need update if line hitbox size is modified
        for x_offset in (-1, 0, 1):
            for y_offset in (-1, 0, 1):
                cell = self.get_cell(
                    point.base.position + self.cell_size * Vector(x_offset, y_offset)
                )

                if cell != None:
                    for line in cell.lines:
                        # Intentionally contains duplicates, ordered by id
                        interacting_lines.append(line)

        return interacting_lines
