from engine.vector import Vector
from engine.contact_point import ContactPoint

ACCELERATION_MULT = 0.1
MAX_LINE_EXTENSION_RATIO = 0.25
LINE_HITBOX_HEIGHT = 10


class PhysicsLine:
    def __init__(
        self,
        id: int,
        p1: Vector,
        p2: Vector,
        flipped: bool,
        left_ext: bool,
        right_ext: bool,
        acceleration: float,
    ) -> None:
        self.id = id
        self.endpoints = (p1.copy(), p2.copy())
        self.flipped = flipped
        self.left_ext = left_ext
        self.right_ext = right_ext
        self.acceleration = acceleration

        # init computed fields
        self.update_computed()

    def update_computed(self):
        # Line as a vector component
        self.vector = self.endpoints[1] - self.endpoints[0]
        # Length of the line
        self.length = self.vector.length()
        # Inverse length squared
        self.inv_length_squared = 1 / self.vector.length_sq()
        # Unit vector pointing along line
        self.unit = self.vector / self.length
        # Unit vector pointing up from the line
        self.normal_unit = self.unit.rot_ccw()
        # Size of extension relative to line length
        self.ext_ratio = min(MAX_LINE_EXTENSION_RATIO, LINE_HITBOX_HEIGHT / self.length)
        # Left and right limits with extension applied
        self.limit_left = 0.0
        self.limit_right = 1.0
        self.acceleration_vector = self.unit * ACCELERATION_MULT * self.acceleration

        if self.flipped:
            self.normal_unit *= -1
            self.acceleration_vector *= -1

        if self.left_ext:
            self.limit_left -= self.ext_ratio

        if self.right_ext:
            self.limit_right += self.ext_ratio

    def set_endpoints(self, p1: Vector, p2: Vector):
        self.endpoints: tuple[Vector, Vector] = (p1.copy(), p2.copy())
        self.update_computed()

    def set_flipped(self, flipped: bool):
        self.flipped = flipped
        self.update_computed()

    def set_extensions(self, left: bool, right: bool):
        self.left_ext = left
        self.right_ext = right
        self.update_computed()

    def interact(self, point: ContactPoint):
        offset_from_point = point.position - self.endpoints[0]
        moving_into_line = (self.normal_unit @ point.velocity) > 0
        dist_from_line_top = self.normal_unit @ offset_from_point
        pos_between_ends = (self.vector @ offset_from_point) * self.inv_length_squared

        # if in line hitbox and moving into line
        if (
            moving_into_line
            and 0 < dist_from_line_top
            and dist_from_line_top < LINE_HITBOX_HEIGHT
            and self.limit_left <= pos_between_ends
            and pos_between_ends <= self.limit_right
        ):
            # collide
            new_position = (
                (self.normal_unit * dist_from_line_top) - point.position
            ) * -1
            friction_vector = (
                self.normal_unit.rot_cw() * point.friction
            ) * dist_from_line_top

            if point.previous_position.x >= new_position.x:
                friction_vector.x *= -1
            if point.previous_position.y < new_position.y:
                friction_vector.y *= -1

            new_previous_position = (
                point.previous_position + friction_vector + self.acceleration_vector
            )

            return (new_position, new_previous_position)
        else:
            return (point.position, point.previous_position)
