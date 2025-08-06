from engine.point import ContactPoint, FlutterPoint

from typing import Union, Optional


# Common bone properties and methods
class BaseBone:
    def __init__(
        self,
        point1: Union[ContactPoint, FlutterPoint],
        point2: Union[ContactPoint, FlutterPoint],
        bias: float,
    ):
        self.point1 = point1
        self.point2 = point2
        # Initial rest length of the bone
        self.rest_length = point1.base.position.distance_from(point2.base.position)
        # Which point gets updated more (0 affects point 1 entirely, 1 affects point 2 entirely)
        self.bias = bias

    def get_vector(self):
        return self.point1.base.position - self.point2.base.position

    def get_adjustment(self):
        current_length = self.get_vector().length()

        if current_length == 0:
            return 0

        return (current_length - self.rest_length) / current_length

    def update_points(self, adjustment):
        bone_vector = self.get_vector()
        self.point1.base.update_state(
            self.point1.base.position - bone_vector * adjustment * (1 - self.bias),
            self.point1.base.velocity,
            self.point1.base.previous_position,
        )
        self.point2.base.update_state(
            self.point2.base.position + bone_vector * adjustment * self.bias,
            self.point2.base.velocity,
            self.point2.base.previous_position,
        )


# Bones connecting points to keep them as the same structure
class NormalBone:
    def __init__(self, point1: ContactPoint, point2: ContactPoint):
        self.base = BaseBone(point1, point2, 0.5)

    def process(self):
        adjustment = self.base.get_adjustment()
        self.base.update_points(adjustment)


# Bones that can break after a certain stretch threshold
# These bones are connected between rider and vehicle points
class MountBone:
    def __init__(self, point1: ContactPoint, point2: ContactPoint, endurance: float):
        self.base = BaseBone(point1, point2, 0.5)
        self.endurance = endurance

    def get_intact(self, remounting: Optional[bool] = None) -> bool:
        adjustment = self.base.get_adjustment()
        endurance = self.endurance

        if remounting:
            endurance *= 2

        return adjustment <= endurance * self.base.rest_length

    def process(self, remounting: Optional[bool] = None):
        adjustment = self.base.get_adjustment()

        strength = 1
        if remounting:
            strength = 0.1

        if self.get_intact(remounting):
            self.base.update_points(adjustment * strength)


# Bones designed to only repel points after a certain fraction of their rest length is reached
class RepelBone:
    def __init__(
        self, point1: ContactPoint, point2: ContactPoint, length_factor: float
    ):
        self.base = BaseBone(point1, point2, 0.5)
        # TODO refactor to keep track of length factor
        self.base.rest_length *= length_factor

    def process(self):
        adjustment = self.base.get_adjustment()

        if self.base.get_vector().length() < self.base.rest_length:
            self.base.update_points(adjustment)


# Non-colliding bone connecting a flutter point to another flutter point or a contact point
class FlutterBone:
    def __init__(self, point1: Union[FlutterPoint, ContactPoint], point2: FlutterPoint):
        self.base = BaseBone(point1, point2, 1)

    def process(self):
        adjustment = self.base.get_adjustment()
        self.base.update_points(adjustment)
