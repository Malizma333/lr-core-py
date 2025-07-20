# TODO remount physics? + remount versions (lra vs .com)?
# TODO scarf physics? + scarf versions (lra vs .com)?

from enum import Enum
from typing import TypedDict, Union
from engine.vector import Vector
import math

MOUNT_BONE_ENDURANCE = 0.057
REPEL_BONE_LENGTH_FACTOR = 0.5


class ContactPoint:
    def __init__(self, position: Vector, velocity: Vector, friction: float):
        self.friction = friction
        self.position = position.copy()
        self.velocity = velocity.copy()
        self.previous_position = position - velocity

    def set_position(self, new_position: Vector):
        self.position = new_position.copy()

    def set_velocity(self, new_velocity: Vector):
        self.velocity = new_velocity.copy()

    def set_prev_position(self, new_prev_position: Vector):
        self.previous_position = new_prev_position.copy()

    def __repr__(self):
        return f"ContactPoint(position: {self.position}, velocity: {self.velocity}, prev_position: {self.previous_position})"


class BaseBone:
    def __init__(self, point1: ContactPoint, point2: ContactPoint):
        self.point1 = point1
        self.point2 = point2
        self.rest_length = point1.position.distance_from(point2.position)


class NormalBone:
    def __init__(self, base: BaseBone):
        self.base = base


class MountBone:
    def __init__(self, base: BaseBone, endurance: float):
        self.base = base
        self.endurance = endurance


class RepelBone:
    def __init__(self, base: BaseBone, length_factor: float):
        self.base = base
        self.length_factor = length_factor
        self.base.rest_length *= length_factor


class EntityState(Enum):
    MOUNTED = 0
    DISMOUNTED = 1


class InitialEntityParams(TypedDict):
    POSITION: Vector
    VELOCITY: Vector
    ROTATION: float
    REMOUNT: bool


class Entity:
    def __init__(self):
        self.bones: list[Union[NormalBone, RepelBone, MountBone]] = []
        self.points: list[ContactPoint] = []
        self.state: EntityState = EntityState.MOUNTED

    def apply_initial_state(
        self, init_state: InitialEntityParams, rotation_origin: Vector
    ):
        # TODO: Remount

        origin = rotation_origin
        cos_theta = math.cos(init_state["ROTATION"])
        sin_theta = math.sin(init_state["ROTATION"])

        for i, point in enumerate(self.points):
            offset = point.position - origin
            self.points[i].set_position(
                Vector(
                    origin.x + offset.x * cos_theta - offset.y * sin_theta,
                    origin.y + offset.x * sin_theta + offset.y * cos_theta,
                )
            )

        for i, point in enumerate(self.points):
            self.points[i].set_position(point.position + init_state["POSITION"])
            self.points[i].set_velocity(point.velocity + init_state["VELOCITY"])
            self.points[i].set_prev_position(
                self.points[i].position - self.points[i].velocity
            )

    def add_point(self, position: Vector, friction: float) -> ContactPoint:
        point = ContactPoint(position, Vector(0, 0), friction)
        self.points.append(point)
        return point

    def add_normal_bone(self, point1: ContactPoint, point2: ContactPoint):
        self.bones.append(NormalBone(BaseBone(point1, point2)))

    def add_mount_bone(
        self, point1: ContactPoint, point2: ContactPoint, endurance: float
    ):
        self.bones.append(MountBone(BaseBone(point1, point2), endurance))

    def add_repel_bone(
        self, point1: ContactPoint, point2: ContactPoint, length_factor: float
    ):
        self.bones.append(RepelBone(BaseBone(point1, point2), length_factor))

    def copy(self):
        new_entity = Entity()
        new_entity.state = self.state
        point_map: dict[ContactPoint, ContactPoint] = {}

        for point in self.points:
            new_point = new_entity.add_point(point.position, point.friction)
            new_point.set_velocity(point.velocity.copy())
            new_point.set_prev_position(point.previous_position.copy())
            point_map[point] = new_point

        for bone in self.bones:
            new_bone_p1 = point_map[bone.base.point1]
            new_bone_p2 = point_map[bone.base.point2]
            if type(bone) == NormalBone:
                new_entity.add_normal_bone(new_bone_p1, new_bone_p2)
            elif type(bone) == MountBone:
                new_entity.add_mount_bone(new_bone_p1, new_bone_p2, bone.endurance)
            elif type(bone) == RepelBone:
                new_entity.add_repel_bone(new_bone_p1, new_bone_p2, bone.length_factor)
            # Copy original rest length
            new_entity.bones[-1].base.rest_length = bone.base.rest_length

        return new_entity

    def process_bone(self, bone):
        position1 = bone.base.point1.position
        position2 = bone.base.point2.position
        bone_vector = position1 - position2
        current_length = bone_vector.length()
        rest_length = bone.base.rest_length

        if type(bone) == RepelBone and current_length >= rest_length:
            return

        if current_length == 0:
            adjustment = 0
        else:
            adjustment = (current_length - rest_length) / current_length * 0.5

        if type(bone) == MountBone and (
            self.state == EntityState.DISMOUNTED
            or adjustment > bone.endurance * rest_length * 0.5
        ):
            self.state = EntityState.DISMOUNTED
            return

        bone_vector = bone_vector * adjustment
        # TODO side effects
        bone.base.point1.set_position(position1 - bone_vector)
        bone.base.point2.set_position(position2 + bone_vector)


def create_default_rider(init_state: InitialEntityParams) -> Entity:
    entity = Entity()

    # Order doesn't really matter, added in this order for ease of conversion
    # to linerider.com order in test cases
    PEG = entity.add_point(Vector(0.0, 0.0), 0.8)
    TAIL = entity.add_point(Vector(0.0, 5.0), 0.0)
    NOSE = entity.add_point(Vector(15.0, 5.0), 0.0)
    STRING = entity.add_point(Vector(17.5, 0.0), 0.0)
    BUTT = entity.add_point(Vector(5.0, 0.0), 0.8)
    SHOULDER = entity.add_point(Vector(5.0, -5.5), 0.8)
    LEFT_HAND = entity.add_point(Vector(11.5, -5.0), 0.1)
    RIGHT_HAND = entity.add_point(Vector(11.5, -5.0), 0.1)
    LEFT_FOOT = entity.add_point(Vector(10.0, 5.0), 0.0)
    RIGHT_FOOT = entity.add_point(Vector(10.0, 5.0), 0.0)

    entity.add_normal_bone(PEG, TAIL)
    entity.add_normal_bone(TAIL, NOSE)
    entity.add_normal_bone(NOSE, STRING)
    entity.add_normal_bone(STRING, PEG)
    entity.add_normal_bone(PEG, NOSE)
    entity.add_normal_bone(STRING, TAIL)
    entity.add_mount_bone(PEG, BUTT, MOUNT_BONE_ENDURANCE)
    entity.add_mount_bone(TAIL, BUTT, MOUNT_BONE_ENDURANCE)
    entity.add_mount_bone(NOSE, BUTT, MOUNT_BONE_ENDURANCE)
    entity.add_normal_bone(SHOULDER, BUTT)
    entity.add_normal_bone(SHOULDER, LEFT_HAND)
    entity.add_normal_bone(SHOULDER, RIGHT_HAND)
    entity.add_normal_bone(BUTT, LEFT_FOOT)
    entity.add_normal_bone(BUTT, RIGHT_FOOT)
    entity.add_normal_bone(SHOULDER, RIGHT_HAND)
    entity.add_mount_bone(SHOULDER, PEG, MOUNT_BONE_ENDURANCE)
    entity.add_mount_bone(STRING, LEFT_HAND, MOUNT_BONE_ENDURANCE)
    entity.add_mount_bone(STRING, RIGHT_HAND, MOUNT_BONE_ENDURANCE)
    entity.add_mount_bone(LEFT_FOOT, NOSE, MOUNT_BONE_ENDURANCE)
    entity.add_mount_bone(RIGHT_FOOT, NOSE, MOUNT_BONE_ENDURANCE)
    entity.add_repel_bone(SHOULDER, LEFT_FOOT, REPEL_BONE_LENGTH_FACTOR)
    entity.add_repel_bone(SHOULDER, RIGHT_FOOT, REPEL_BONE_LENGTH_FACTOR)

    entity.apply_initial_state(init_state, TAIL.position)

    return entity
