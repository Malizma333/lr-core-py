from engine.vector import Vector
from engine.constants import USE_COM_SCARF

import math


# Common point properties and methods
class BasePoint:
    def __init__(
        self, position: Vector, velocity: Vector, previous_position: Vector, id: int
    ):
        self.position = position.copy()
        self.velocity = velocity.copy()
        # Previous position is not necessarily (position - velocity), as it's
        # used to track effects of friction and acceleration
        self.previous_position = previous_position.copy()
        # Index used to identify points within the entity during a deep copy
        self.index = id

    # Function used to update contact points, as multiple properties often get updated at once
    def update_state(self, new_pos: Vector, new_vel: Vector, new_prev_pos: Vector):
        self.position = new_pos.copy()
        self.velocity = new_vel.copy()
        self.previous_position = new_prev_pos.copy()


# Colliding point of an entity
class ContactPoint:
    def __init__(
        self,
        base_point: BasePoint,
        friction: float,
    ):
        self.base = base_point
        self.friction = friction

    def initial_step(self, gravity: Vector):
        new_velocity = self.base.position - self.base.previous_position + gravity
        current_position = self.base.position
        self.base.update_state(
            current_position + new_velocity, new_velocity, current_position
        )


# Non-colliding point of an entity, used for the scarf
class FlutterPoint:
    def __init__(
        self,
        base: BasePoint,
        air_friction: float,
    ):
        self.base = base
        self.air_friction = air_friction

    # glsl pseudo-randomness
    def rand(self, seed):
        next = math.sin(seed @ Vector(12.9898, 78.233)) * 43758.5453
        return next - math.trunc(next)

    def get_flutter(self, velocity: Vector, seed_value: Vector):
        # Smaller value means more flutter as speed increases
        SPEED_THRESHOLD = 40
        # Intensity of length change
        INTENSITY = 2

        speed = velocity.length_sq() ** 0.25
        random_length = self.rand(velocity)
        random_angle = self.rand(seed_value)
        random_length *= INTENSITY * speed * -math.expm1(-speed / SPEED_THRESHOLD)
        random_angle *= 2 * math.pi
        return random_length * Vector(math.cos(random_angle), math.sin(random_angle))

    def initial_step(self, gravity: Vector):
        computed_velocity = self.base.position - self.base.previous_position
        new_velocity = (computed_velocity * (1 - self.air_friction)) + gravity
        current_position = self.base.position
        new_position = current_position + new_velocity

        if USE_COM_SCARF:
            new_position = self.get_flutter(new_velocity, current_position)

        self.base.update_state(new_position, new_velocity, current_position)
