from engine.grid import Grid
from engine.vector import Vector
from engine.point import BasePoint, ContactPoint, FlutterPoint
from engine.bone import BaseBone, NormalBone, RepelBone, MountBone, FlutterChain
from engine.joint import Joint
from engine.constants import USE_COM_SCARF

from typing import TypedDict, Union
import math

# TODO remounting .com v1, .com v2, lra
#   pre-remount (indicated with "remountable": undefined) the tail fakie breaks the sled after dismount
#   remount-v1 (indicated with "remountable": true) the tail fakie does not break the sled after dismount (bug)
#   remount-v2 (indicated with "remountable": 1) the tail fakie breaks the sled after dismount (fixed)
#   lra ???
# TODO lra fakie bug
#   sled breaks for shoulder fakie (which it shouldn't, according to flash)
#   sled doesn't ever break if bosh is dismounted (which it should still do for tail fakies, according to current .com)


class InitialEntityParams(TypedDict):
    POSITION: Vector
    VELOCITY: Vector
    ROTATION: float  # In degrees
    REMOUNT: bool


# A base entity that holds the skeleton
class BaseEntity:
    def __init__(self):
        self.contact_points: list[ContactPoint] = []
        self.flutter_points: list[FlutterPoint] = []
        self.normal_bones: list[NormalBone] = []
        self.repel_bones: list[RepelBone] = []
        self.flutter_chains: list[FlutterChain] = []

    def add_contact_point(self, position: Vector, friction: float) -> ContactPoint:
        base_point = BasePoint(
            position, Vector(0, 0), position, len(self.contact_points)
        )
        point = ContactPoint(base_point, friction)
        self.contact_points.append(point)
        return point

    def add_flutter_point(self, position: Vector, air_friction: float) -> FlutterPoint:
        base_point = BasePoint(
            position, Vector(0, 0), position, len(self.flutter_points)
        )
        point = FlutterPoint(base_point, air_friction)
        self.flutter_points.append(point)
        return point

    def add_normal_bone(
        self,
        point1: ContactPoint,
        point2: ContactPoint,
    ) -> NormalBone:
        bone = NormalBone(BaseBone(point1, point2))
        self.normal_bones.append(bone)
        return bone

    def add_repel_bone(
        self,
        point1: ContactPoint,
        point2: ContactPoint,
        length_factor: float,
    ) -> RepelBone:
        bone = RepelBone(BaseBone(point1, point2), length_factor)
        self.repel_bones.append(bone)
        return bone

    def add_flutter_chain(
        self, points: list[FlutterPoint], attachment: ContactPoint
    ) -> FlutterChain:
        chain = FlutterChain(points, attachment)
        self.flutter_chains.append(chain)
        return chain


class RiderEntity:
    def __init__(self, base: BaseEntity):
        self.base = base
        self.can_remount = False


class VehicleEntity:
    def __init__(self, base: BaseEntity):
        self.base = base
        self.can_remount = False
        self.intact = True
        self.joints: list[Joint] = []

    def add_joint(self, bone1: BaseBone, bone2: BaseBone):
        self.joints.append(Joint(bone1, bone2))

    def process_joints(self):
        for joint in self.joints:
            if self.intact and joint.should_break():
                self.intact = False


# A rider and vehicle pair with mounted context between them
class RiderVehiclePair:
    def __init__(
        self,
        rider: RiderEntity,
        vehicle: VehicleEntity,
    ):
        self.rider = rider
        self.vehicle = vehicle
        self.rider_mount_bones: list[MountBone] = []
        self.vehicle_mount_bones: list[MountBone] = []
        self.joints: list[Joint] = []
        self.mounted = True

    # Copy is used for deep copying entity states after each frame
    def copy(self):
        # TODO
        return self

    def add_rider_mount_bone(
        self,
        point1: ContactPoint,
        point2: ContactPoint,
        endurance: float,
    ) -> MountBone:
        bone = MountBone(BaseBone(point1, point2), endurance)
        self.rider_mount_bones.append(bone)
        return bone

    def add_vehicle_mount_bone(
        self,
        point1: ContactPoint,
        point2: ContactPoint,
        endurance: float,
    ) -> MountBone:
        bone = MountBone(BaseBone(point1, point2), endurance)
        self.vehicle_mount_bones.append(bone)
        return bone

    def add_joint(self, bone1: BaseBone, bone2: BaseBone):
        self.joints.append(Joint(bone1, bone2))

    # This updates the contact points with initial position, velocity, and a rotation
    # about the tail, as well as setting the remount property
    def apply_initial_state(
        self, init_state: InitialEntityParams, rotation_origin: Vector
    ):
        self.vehicle.can_remount = init_state["REMOUNT"]
        self.rider.can_remount = init_state["REMOUNT"]

        origin = rotation_origin
        # Note that the use of cos and sin here is not exactly the same as javascript
        # engines might implement it
        # This gets tested with 50 degrees so it happens to pass the test case,
        # but this may not give the same output for every input
        # TODO standard sin/cos implementation?
        cos_theta = math.cos(init_state["ROTATION"] * math.pi / 180)
        sin_theta = math.sin(init_state["ROTATION"] * math.pi / 180)

        for point in self.get_all_points():
            offset = point.position - origin
            point.update_state(
                Vector(
                    origin.x + offset.x * cos_theta - offset.y * sin_theta,
                    origin.y + offset.x * sin_theta + offset.y * cos_theta,
                ),
                point.velocity,
                point.previous_position,
            )

        for point in self.get_all_points():
            start_position = point.position + init_state["POSITION"]
            start_velocity = point.velocity + init_state["VELOCITY"]
            point.update_state(
                start_position, start_velocity, start_position - start_velocity
            )

    def process_initial_step(self, gravity: Vector):
        for point in self.vehicle.base.contact_points:
            point.initial_step(gravity)

        for point in self.rider.base.contact_points:
            point.initial_step(gravity)

        for point in self.vehicle.base.flutter_points:
            point.initial_step(gravity)

        for point in self.rider.base.flutter_points:
            point.initial_step(gravity)

    def process_bones(self):
        for bone in self.vehicle.base.normal_bones:
            bone.process()

        for bone in self.vehicle_mount_bones:
            if self.mounted:
                intact = bone.process()
                if not intact:
                    self.mounted = False

        for bone in self.vehicle.base.repel_bones:
            bone.process()

        for bone in self.rider.base.normal_bones:
            bone.process()

        for bone in self.rider_mount_bones:
            if self.mounted:
                intact = bone.process()
                if not intact:
                    self.mounted = False

        for bone in self.rider.base.repel_bones:
            bone.process()

    def process_collisions(self, grid: Grid):
        contact_points = (
            self.vehicle.base.contact_points + self.rider.base.contact_points
        )

        for point in contact_points:
            interacting_lines = grid.get_interacting_lines(point)
            for line in interacting_lines:
                new_pos, new_prev_pos = line.interact(point)
                point.base.update_state(new_pos, point.base.velocity, new_prev_pos)

    def process_joints(self):
        for joint in self.joints:
            if self.mounted and joint.should_break():
                self.mounted = False

        self.vehicle.process_joints()

    def process_flutter(self):
        for chain in self.vehicle.base.flutter_chains:
            chain.process()

        for chain in self.rider.base.flutter_chains:
            chain.process()

    def get_all_points(self) -> list[BasePoint]:
        all_points = []

        for contact_point in (
            self.vehicle.base.contact_points + self.rider.base.contact_points
        ):
            all_points.append(contact_point.base)

        for flutter_point in (
            self.vehicle.base.flutter_points + self.rider.base.flutter_points
        ):
            all_points.append(flutter_point.base)

        return all_points


def create_default_rider(init_state: InitialEntityParams) -> RiderVehiclePair:
    rider = RiderEntity(BaseEntity())
    sled = VehicleEntity(BaseEntity())
    rider_sled_pair = RiderVehiclePair(rider, sled)

    DEFAULT_MOUNT_ENDURANCE = 0.057
    DEFAULT_REPEL_LENGTH_FACTOR = 0.5

    if USE_COM_SCARF:
        SCARF_FRICTION = 0.2
    else:
        SCARF_FRICTION = 0.1

    # Create the contact points first, at their initial positions
    # Order doesn't really matter, added in this order to match linerider.com
    # based test cases
    # Sled points
    PEG = sled.base.add_contact_point(Vector(0.0, 0.0), 0.8)
    TAIL = sled.base.add_contact_point(Vector(0.0, 5.0), 0.0)
    NOSE = sled.base.add_contact_point(Vector(15.0, 5.0), 0.0)
    STRING = sled.base.add_contact_point(Vector(17.5, 0.0), 0.0)

    # Rider points
    BUTT = rider.base.add_contact_point(Vector(5.0, 0.0), 0.8)
    SHOULDER = rider.base.add_contact_point(Vector(5.0, -5.5), 0.8)
    RIGHT_HAND = rider.base.add_contact_point(Vector(11.5, -5.0), 0.1)
    LEFT_HAND = rider.base.add_contact_point(Vector(11.5, -5.0), 0.1)
    LEFT_FOOT = rider.base.add_contact_point(Vector(10.0, 5.0), 0.0)
    RIGHT_FOOT = rider.base.add_contact_point(Vector(10.0, 5.0), 0.0)
    SCARF_0 = rider.base.add_flutter_point(Vector(3, -5.5), SCARF_FRICTION)
    SCARF_1 = rider.base.add_flutter_point(Vector(1, -5.5), SCARF_FRICTION)
    SCARF_2 = rider.base.add_flutter_point(Vector(-1, -5.5), SCARF_FRICTION)
    SCARF_3 = rider.base.add_flutter_point(Vector(-3, -5.5), SCARF_FRICTION)
    SCARF_4 = rider.base.add_flutter_point(Vector(-5, -5.5), SCARF_FRICTION)
    SCARF_5 = rider.base.add_flutter_point(Vector(-7, -5.5), SCARF_FRICTION)
    SCARF_6 = rider.base.add_flutter_point(Vector(-9, -5.5), SCARF_FRICTION)

    # Sled bones
    SLED_BACK = sled.base.add_normal_bone(PEG, TAIL)
    sled.base.add_normal_bone(TAIL, NOSE)
    sled.base.add_normal_bone(NOSE, STRING)
    SLED_FRONT = sled.base.add_normal_bone(STRING, PEG)
    sled.base.add_normal_bone(PEG, NOSE)
    sled.base.add_normal_bone(STRING, TAIL)
    rider_sled_pair.add_vehicle_mount_bone(PEG, BUTT, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_vehicle_mount_bone(TAIL, BUTT, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_vehicle_mount_bone(NOSE, BUTT, DEFAULT_MOUNT_ENDURANCE)

    # Rider bones
    TORSO = rider.base.add_normal_bone(SHOULDER, BUTT)
    rider.base.add_normal_bone(SHOULDER, LEFT_HAND)
    rider.base.add_normal_bone(SHOULDER, RIGHT_HAND)
    rider.base.add_normal_bone(BUTT, LEFT_FOOT)
    rider.base.add_normal_bone(BUTT, RIGHT_FOOT)
    rider.base.add_normal_bone(SHOULDER, RIGHT_HAND)
    rider_sled_pair.add_rider_mount_bone(SHOULDER, PEG, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_rider_mount_bone(STRING, LEFT_HAND, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_rider_mount_bone(STRING, RIGHT_HAND, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_rider_mount_bone(LEFT_FOOT, NOSE, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_rider_mount_bone(RIGHT_FOOT, NOSE, DEFAULT_MOUNT_ENDURANCE)
    rider.base.add_repel_bone(SHOULDER, LEFT_FOOT, DEFAULT_REPEL_LENGTH_FACTOR)
    rider.base.add_repel_bone(SHOULDER, RIGHT_FOOT, DEFAULT_REPEL_LENGTH_FACTOR)
    rider.base.add_flutter_chain(
        [SCARF_0, SCARF_1, SCARF_2, SCARF_3, SCARF_4, SCARF_5, SCARF_6], SHOULDER
    )

    # Add the bindings with their joints
    rider_sled_pair.add_joint(TORSO.base, SLED_FRONT.base)
    rider_sled_pair.add_joint(SLED_BACK.base, SLED_FRONT.base)
    sled.add_joint(SLED_BACK.base, SLED_FRONT.base)

    # Apply initial state once everything is initialized
    # Note that this must be applied after bone rest lengths are calculated
    # because it does not affect bone rest lengths
    rider_sled_pair.apply_initial_state(init_state, TAIL.base.position)

    return rider_sled_pair
