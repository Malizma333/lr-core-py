from engine.point import ContactPoint, FlutterPoint

from typing import Union, Optional


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


# Bones that can break after a certain stretch threshold
# These bones are connected between rider and vehicle points
class MountBone:
    def __init__(self, base: BaseBone, endurance: float):
        self.base = base
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
    def __init__(self, base: BaseBone, length_factor: float):
        self.base = base
        self.base.rest_length *= length_factor

    def process(self):
        adjustment = self.base.get_adjustment()

        if self.base.get_vector().length() < self.base.rest_length:
            self.base.update_points(adjustment)


# Non-colliding chain of bones connecting flutter points to a contact point
class FlutterChain:
    def __init__(self, points: list[FlutterPoint], attachment: ContactPoint):
        self.bone_chain: list[BaseBone] = []
        self.bone_chain.append(BaseBone(attachment, points[0]))
        for i in range(len(points) - 1):
            self.bone_chain.append(BaseBone(points[i], points[i + 1]))

    def process(self):
        for bone in self.bone_chain:
            adjustment = bone.get_adjustment()
            next_position = bone.get_vector() * adjustment + bone.point2.base.position
            bone.point2.base.update_state(
                next_position,
                bone.point2.base.velocity,
                bone.point2.base.previous_position,
            )
