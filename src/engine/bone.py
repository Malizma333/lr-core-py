from engine.point import BasePoint
from enum import Enum


class BoneType(Enum):
    NORMAL = 0
    MOUNT = 1
    REPEL = 2
    FLUTTER = 3


# Common bone properties and methods
class BaseBone:
    def __init__(
        self, point1: BasePoint, point2: BasePoint, bias: float, length_factor: float
    ):
        self.point1 = point1
        self.point2 = point2
        # Initial rest length of the bone
        self.rest_length = (
            point1.position.distance_from(point2.position) * length_factor
        )
        # Which point gets updated more (0 affects point 1 entirely, 1 affects point 2 entirely)
        self.bias = bias

    def get_vector(self):
        return self.point1.position - self.point2.position

    def get_adjustment(self):
        current_length = self.get_vector().length()

        if current_length == 0:
            return 0

        return (current_length - self.rest_length) / current_length

    def update_points(self, adjustment):
        bone_vector = self.get_vector()
        self.point1.update_state(
            self.point1.position - bone_vector * adjustment * (1 - self.bias),
            self.point1.velocity,
            self.point1.previous_position,
        )
        self.point2.update_state(
            self.point2.position + bone_vector * adjustment * self.bias,
            self.point2.velocity,
            self.point2.previous_position,
        )


# Bones connecting points to keep them as the same structure
class NormalBone:
    def __init__(self, point1: BasePoint, point2: BasePoint):
        self.base = BaseBone(point1, point2, 0.5, 1)

    def process(self, adjustment_strength: float):
        adjustment = self.base.get_adjustment()
        self.base.update_points(adjustment * adjustment_strength)


# Bones designed to only repel points after a certain rest length is reached
class RepelBone:
    def __init__(self, point1: BasePoint, point2: BasePoint, length_factor: float):
        self.base = BaseBone(point1, point2, 0.5, length_factor)

    def process(self, adjustment_strength: float):
        adjustment = self.base.get_adjustment()
        if self.base.get_vector().length() < self.base.rest_length:
            self.base.update_points(adjustment * adjustment_strength)


class FlutterBone:
    def __init__(self, point1: BasePoint, point2: BasePoint):
        self.base = BaseBone(point1, point2, 1, 1)

    def process(self):
        adjustment = self.base.get_adjustment()
        self.base.update_points(adjustment)


# Bones that can break after a certain stretch threshold
# These bones are connected between two skeletons
class MountBone:
    def __init__(self, point1: BasePoint, point2: BasePoint, endurance: float):
        self.base = BaseBone(point1, point2, 0.5, 1)
        self.endurance = endurance

    def get_intact(self, remounting: bool) -> bool:
        REMOUNT_ENDURANCE_FACTOR = 2
        adjustment = self.base.get_adjustment()
        endurance = self.endurance
        if remounting:
            endurance *= REMOUNT_ENDURANCE_FACTOR
        return adjustment <= endurance * self.base.rest_length

    def process(self, adjustment_strength: float):
        adjustment = self.base.get_adjustment()
        self.base.update_points(adjustment * adjustment_strength)
