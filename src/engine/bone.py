from typing import Union
from engine.point import ContactPoint, FlutterPoint
from engine.binding import Binding


# Common bone properties and methods
class BaseBone:
    def __init__(
        self,
        point1: Union[ContactPoint, FlutterPoint],
        point2: Union[ContactPoint, FlutterPoint],
    ):
        self.point1 = point1
        self.point2 = point2
        self.rest_length = point1.base.position.distance_from(point2.base.position)
        self.bias = 0.5

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
            self.point1.base.position - bone_vector * adjustment * self.bias,
            self.point1.base.velocity,
            self.point1.base.previous_position,
        )
        self.point2.base.update_state(
            self.point2.base.position + bone_vector * adjustment * (1 - self.bias),
            self.point2.base.velocity,
            self.point2.base.previous_position,
        )


# Bones connecting points to keep them as the same structure
class NormalBone:
    def __init__(self, base: BaseBone):
        self.base = base

    def process(self):
        adjustment = self.base.get_adjustment()
        self.base.update_points(adjustment)


# Bones that can also break after a certain threshold
class FragileBone:
    def __init__(self, base: BaseBone, endurance: float, binding: Binding):
        self.base = base
        self.endurance = endurance
        self.binding = binding

    def process(self):
        adjustment = self.base.get_adjustment()

        if (
            not self.binding.get_intact()
            or adjustment > self.endurance * self.base.rest_length
        ):
            self.binding.set_intact(False)
            return

        self.base.update_points(adjustment)


# Bones designed to only repel points after a certain fraction of their rest length is reached
class RepelBone:
    def __init__(self, base: BaseBone, length_factor: float):
        self.base = base
        self.base.rest_length *= length_factor

    def process(self):
        adjustment = self.base.get_adjustment()

        if self.base.get_vector().length() >= self.base.rest_length:
            return

        self.base.update_points(adjustment)


# Non-colliding bones connecting flutter points
class FlutterBone:
    def __init__(self, base: BaseBone):
        self.base = base

    def process(self):
        adjustment = self.base.get_adjustment()
        point2 = self.base.point2
        next_position = self.base.get_vector() * adjustment + point2.base.position
        self.base.point2.base.update_state(
            next_position, point2.base.velocity, point2.base.previous_position
        )


# Connects a contact point to a flutter point
class FlutterConnectorBone:
    def __init__(self, base: BaseBone) -> None:
        self.base = base

    def process(self):
        adjustment = self.base.get_adjustment()
        point2 = self.base.point2
        next_position = self.base.get_vector() * adjustment + point2.base.position
        self.base.point2.base.update_state(
            next_position, point2.base.velocity, point2.base.previous_position
        )
