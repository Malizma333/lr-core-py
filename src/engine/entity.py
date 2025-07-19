# TODO remount physics? + remount versions (lra vs .com)?
# TODO scarf physics? + scarf versions (lra vs .com)?

from enum import Enum
from typing import TypedDict, Union
from engine.vector import Vector
import math


class ContactPoint:
    def __init__(self, position: Vector, velocity: Vector, friction: float):
        self.position = position
        self.velocity = velocity
        self.friction = friction


class BaseBone(TypedDict):
    POINT1: ContactPoint
    POINT2: ContactPoint
    RESTING_LENGTH: float


class NormalBone(TypedDict):
    BASE: BaseBone


class MountBone(TypedDict):
    BASE: BaseBone
    ENDURANCE: float


class RepelBone(TypedDict):
    BASE: BaseBone
    LENGTH_FACTOR: float


Bone = Union[NormalBone, RepelBone, MountBone]


class EntityState(Enum):
    MOUNTED = 0
    DISMOUNTED = 1


class InitialEntityParams(TypedDict):
    POSITION: Vector
    VELOCITY: Vector
    ROTATION: float
    REMOUNT: bool


BONE_ENDURANCE = 0.0285
MOUNT_ENDURANCE = 0.057
REPEL_FACTOR = 0.5


class Entity:
    def __init__(self):
        self.bones: list[Bone] = []
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
            self.points[i].position = Vector(
                origin.x + offset.x * cos_theta - offset.y * sin_theta,
                origin.y + offset.x * sin_theta + offset.y * cos_theta,
            )

        for i in range(len(self.points)):
            self.points[i].position += init_state["POSITION"]
            self.points[i].velocity += init_state["VELOCITY"]

    def add_point(self, position: Vector, friction: float) -> ContactPoint:
        point = ContactPoint(position, Vector(0, 0), friction)
        self.points.append(point)
        return point

    def add_normal_bone(self, point1: ContactPoint, point2: ContactPoint):
        bone: NormalBone = {"BASE": self.create_base_bone(point1, point2)}
        self.bones.append(bone)

    def add_mount_bone(
        self, point1: ContactPoint, point2: ContactPoint, endurance: float
    ):
        bone: MountBone = {
            "BASE": self.create_base_bone(point1, point2),
            "ENDURANCE": endurance,
        }
        self.bones.append(bone)

    def add_repel_bone(
        self, point1: ContactPoint, point2: ContactPoint, length_factor: float
    ):
        bone: RepelBone = {
            "BASE": self.create_base_bone(point1, point2),
            "LENGTH_FACTOR": length_factor,
        }
        self.bones.append(bone)

    def create_base_bone(self, point1: ContactPoint, point2: ContactPoint) -> BaseBone:
        base: BaseBone = {
            "POINT1": point1,
            "POINT2": point2,
            "RESTING_LENGTH": point1.position.distance_from(point2.position),
        }
        return base

    def copy(self):
        new_entity = Entity()
        new_entity.state = self.state
        point_map: dict[ContactPoint, ContactPoint] = {}

        for point in self.points:
            new_point = new_entity.add_point(point.position, point.friction)
            new_point.velocity = point.velocity.copy()
            point_map[point] = new_point

        for bone in self.bones:
            new_bone_p1 = point_map[bone["BASE"]["POINT1"]]
            new_bone_p2 = point_map[bone["BASE"]["POINT2"]]
            if type(bone) == NormalBone:
                new_entity.add_normal_bone(new_bone_p1, new_bone_p2)
            elif type(bone) == MountBone:
                new_entity.add_mount_bone(new_bone_p1, new_bone_p2, bone["ENDURANCE"])
            elif type(bone) == RepelBone:
                new_entity.add_repel_bone(
                    new_bone_p1, new_bone_p2, bone["LENGTH_FACTOR"]
                )

        return new_entity

    def process_bones(self):
        for bone in self.bones:
            position1 = bone["BASE"]["POINT1"].position
            position2 = bone["BASE"]["POINT2"].position
            delta = position1 - position2
            magnitude = delta.magnitude()
            rest_length = bone["BASE"]["RESTING_LENGTH"]

            if type(bone) == RepelBone:
                rest_length *= bone["LENGTH_FACTOR"]

            if type(bone) != RepelBone or magnitude < rest_length:
                if magnitude * 0.5 != 0:
                    scalar = (magnitude - rest_length) / magnitude * 0.5
                else:
                    scalar = 0

                if type(bone) == MountBone and (
                    self.state == EntityState.DISMOUNTED
                    or scalar > rest_length * BONE_ENDURANCE
                ):
                    self.state = EntityState.DISMOUNTED
                else:
                    bone["BASE"]["POINT1"].position -= delta * scalar
                    bone["BASE"]["POINT2"].position += delta * scalar


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
    RIGHT_HAND = entity.add_point(Vector(11.5, -5.0), 0.1)
    LEFT_HAND = entity.add_point(Vector(11.5, -5.0), 0.1)
    LEFT_FOOT = entity.add_point(Vector(10.0, 5.0), 0.0)
    RIGHT_FOOT = entity.add_point(Vector(10.0, 5.0), 0.0)

    entity.add_normal_bone(PEG, TAIL)
    entity.add_normal_bone(TAIL, NOSE)
    entity.add_normal_bone(NOSE, STRING)
    entity.add_normal_bone(STRING, PEG)
    entity.add_mount_bone(PEG, BUTT, MOUNT_ENDURANCE)
    entity.add_mount_bone(TAIL, BUTT, MOUNT_ENDURANCE)
    entity.add_mount_bone(NOSE, BUTT, MOUNT_ENDURANCE)
    entity.add_normal_bone(SHOULDER, BUTT)
    entity.add_normal_bone(SHOULDER, LEFT_HAND)
    entity.add_normal_bone(SHOULDER, RIGHT_HAND)
    entity.add_normal_bone(BUTT, LEFT_FOOT)
    entity.add_normal_bone(BUTT, RIGHT_FOOT)
    entity.add_mount_bone(SHOULDER, PEG, MOUNT_ENDURANCE)
    entity.add_mount_bone(STRING, LEFT_HAND, MOUNT_ENDURANCE)
    entity.add_mount_bone(STRING, RIGHT_HAND, MOUNT_ENDURANCE)
    entity.add_mount_bone(LEFT_FOOT, NOSE, MOUNT_ENDURANCE)
    entity.add_mount_bone(RIGHT_FOOT, NOSE, MOUNT_ENDURANCE)
    entity.add_repel_bone(SHOULDER, LEFT_FOOT, REPEL_FACTOR)
    entity.add_repel_bone(SHOULDER, RIGHT_FOOT, REPEL_FACTOR)

    entity.apply_initial_state(init_state, TAIL.position)

    return entity
