from engine.grid import Grid
from engine.vector import Vector
from engine.point import BasePoint, ContactPoint, FlutterPoint
from engine.bone import NormalBone, RepelBone, MountBone, FlutterBone, BaseBone
from engine.joint import Joint
from engine.flags import LR_COM_SCARF, LRA_LEGACY_FAKIE_CHECK, LRA_REMOUNT

from enum import Enum
from typing import TypedDict, Union
import math


class InitialEntityParams(TypedDict):
    POSITION: Vector
    VELOCITY: Vector
    ROTATION: float  # In degrees
    REMOUNT: bool


class RemountVersion(Enum):
    # pre-remount (indicated with "remountable": undefined) the tail fakie breaks the sled after dismount
    NONE = 0
    # remount-v1 (indicated with "remountable": true) the tail fakie does not break the sled after dismount (bug)
    COM_V1 = 1
    # remount-v2 (indicated with "remountable": 1) the tail fakie breaks the sled after dismount (fixed)
    COM_V2 = 2
    # lra implements its own version of remounting
    LRA = 3


class MountState(Enum):
    MOUNTED = 0
    DISMOUNTING = 1
    DISMOUNTED = 2
    REMOUNTING = 3


# A base entity that holds the skeleton
class BaseEntity:
    def __init__(self, remount_enabled):
        self.contact_points: list[ContactPoint] = []
        self.flutter_points: list[FlutterPoint] = []
        self.normal_bones: list[NormalBone] = []
        self.repel_bones: list[RepelBone] = []
        self.flutter_bones: list[FlutterBone] = []
        self.joints: list[Joint] = []
        self.intact = True
        self.remount_enabled = remount_enabled

    def add_contact_point(self, position: Vector, friction: float) -> ContactPoint:
        base_point = BasePoint(position, Vector(0, 0), position)
        point = ContactPoint(base_point, friction)
        self.contact_points.append(point)
        return point

    def add_flutter_point(self, position: Vector, air_friction: float) -> FlutterPoint:
        base_point = BasePoint(position, Vector(0, 0), position)
        point = FlutterPoint(base_point, air_friction)
        self.flutter_points.append(point)
        return point

    def add_normal_bone(self, point1: ContactPoint, point2: ContactPoint) -> NormalBone:
        bone = NormalBone(point1, point2)
        self.normal_bones.append(bone)
        return bone

    def add_repel_bone(
        self, point1: ContactPoint, point2: ContactPoint, length_factor: float
    ) -> RepelBone:
        bone = RepelBone(point1, point2, length_factor)
        self.repel_bones.append(bone)
        return bone

    def add_flutter_bone(
        self, point1: Union[FlutterPoint, ContactPoint], point2: FlutterPoint
    ) -> FlutterBone:
        bone = FlutterBone(point1, point2)
        self.flutter_bones.append(bone)
        return bone

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
        rider: BaseEntity,
        vehicle: BaseEntity,
        mount_joint_version: RemountVersion,
    ):
        self.rider = rider
        self.vehicle = vehicle
        self.rider_mount_bones: list[MountBone] = []
        self.vehicle_mount_bones: list[MountBone] = []
        self.joints: list[Joint] = []
        self.mount_state = MountState.MOUNTED
        self.frames_until_dismounted = 0
        self.frames_until_remounting = 0
        self.frames_until_mounted = 0
        self.dismounted_this_frame = False
        self.remount_version = mount_joint_version

        if LRA_REMOUNT:
            self.remount_version = RemountVersion.LRA

    # Copy is used for deep copying entity states after each frame
    def copy(self):
        # TODO clean way to deep copy
        return self

    def add_rider_mount_bone(
        self,
        rider_point: ContactPoint,
        vehicle_point: ContactPoint,
        endurance: float,
    ) -> MountBone:
        bone = MountBone(rider_point, vehicle_point, endurance)
        self.rider_mount_bones.append(bone)
        return bone

    def add_vehicle_mount_bone(
        self,
        vehicle_point: ContactPoint,
        rider_point: ContactPoint,
        endurance: float,
    ) -> MountBone:
        bone = MountBone(vehicle_point, rider_point, endurance)
        self.vehicle_mount_bones.append(bone)
        return bone

    def add_joint(self, bone1: BaseBone, bone2: BaseBone):
        self.joints.append(Joint(bone1, bone2))

    # This updates the contact points with initial position, velocity, and a rotation
    # about the tail, as well as setting the remount property
    def apply_initial_state(
        self, init_state: InitialEntityParams, rotation_origin: Vector
    ):
        origin = rotation_origin
        # Note that the use of cos and sin here is not exactly the same as javascript
        # engines might implement it (which usually use system calls anyway)
        # This gets tested with 50 degrees so it happens to pass the test case,
        # but this may not give the same output for every input
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

    def is_mounted(self):
        return (
            self.mount_state == MountState.MOUNTED
            or self.mount_state == MountState.REMOUNTING
        )

    def transition_to_mount_state(self, new_mount_state: MountState, reset_timer: bool):
        # Sets the new state while safely resetting timers
        if new_mount_state == MountState.DISMOUNTING and reset_timer:
            self.frames_until_dismounted = 30
        elif new_mount_state == MountState.DISMOUNTED and reset_timer:
            self.frames_until_remounting = 3
        elif new_mount_state == MountState.REMOUNTING and reset_timer:
            self.frames_until_mounted = 3

        self.mount_state = new_mount_state

    def dismount(self):
        self.dismounted_this_frame = True
        if self.remount_version == RemountVersion.NONE:
            # Just dismount, ignore timers
            self.transition_to_mount_state(MountState.DISMOUNTED, False)
        else:
            if self.mount_state == MountState.MOUNTED:
                # Dismount with timer until next remount
                self.transition_to_mount_state(MountState.DISMOUNTING, True)
            elif self.mount_state == MountState.REMOUNTING:
                # Revert from remounting to dismounted without timer
                self.transition_to_mount_state(MountState.DISMOUNTED, True)

    def process_initial_step(self, gravity: Vector):
        for point in self.vehicle.contact_points:
            point.initial_step(gravity)

        for point in self.rider.contact_points:
            point.initial_step(gravity)

        for point in self.vehicle.flutter_points:
            point.initial_step(gravity)

        for point in self.rider.flutter_points:
            point.initial_step(gravity)

    def process_bones(self):
        for bone in self.vehicle.normal_bones:
            bone.process()

        for bone in self.vehicle_mount_bones:
            if self.is_mounted():
                remounting = self.mount_state == MountState.REMOUNTING
                intact = bone.get_intact(remounting)
                bone.process(remounting)
                if not intact:
                    self.dismount()

        for bone in self.vehicle.repel_bones:
            bone.process()

        for bone in self.rider.normal_bones:
            bone.process()

        for bone in self.rider_mount_bones:
            if self.is_mounted():
                remounting = self.mount_state == MountState.REMOUNTING
                intact = bone.get_intact(remounting)
                bone.process(remounting)
                if not intact:
                    self.dismount()

        for bone in self.rider.repel_bones:
            bone.process()

    def process_collisions(self, grid: Grid):
        contact_points: list[ContactPoint] = []

        for point in self.vehicle.contact_points:
            contact_points.append(point)

        for point in self.rider.contact_points:
            contact_points.append(point)

        for point in contact_points:
            interacting_lines = grid.get_interacting_lines(point)
            for line in interacting_lines:
                new_pos, new_prev_pos = line.interact(point)
                point.base.update_state(new_pos, point.base.velocity, new_prev_pos)

    def process_flutter(self):
        for chain in self.vehicle.flutter_bones:
            chain.process()

        for chain in self.rider.flutter_bones:
            chain.process()

    def process_joints(self):
        if LRA_LEGACY_FAKIE_CHECK:
            # Don't process joints if dismounted
            if not self.is_mounted():
                return

        for joint in self.joints:
            if self.is_mounted() and joint.should_break():
                self.dismount()

        if self.remount_version == RemountVersion.COM_V1:
            # Don't process vehicle joints if dismounted
            if self.is_mounted():
                self.vehicle.process_joints()
        else:
            # Process vehicle joints regardless
            self.vehicle.process_joints()

        # Process rider joints (default has none)
        self.rider.process_joints()

    # Checks if either remounting or mounted states can be entered by checking
    # that the bone stays intact with different strength/endurance remount values
    def can_enter_state(self, state: MountState):
        remounting = state == MountState.REMOUNTING

        for bone in self.vehicle_mount_bones:
            if not bone.get_intact(remounting):
                return False

        for bone in self.rider_mount_bones:
            if not bone.get_intact(remounting):
                return False

        for joint in self.vehicle.joints:
            if joint.should_break():
                return False

        for joint in self.rider.joints:
            if joint.should_break():
                return False

        for joint in self.joints:
            if joint.should_break():
                return False

        return True

    # Checks if this rider-vehicle pair has a vehicle available for swapping
    def vehicle_available(self):
        return (
            self.vehicle.intact
            and self.vehicle.remount_enabled
            and not self.is_mounted()
        )

    def process_remount(self):
        if (
            self.remount_version == RemountVersion.NONE
            or self.rider.remount_enabled == False
        ):
            return

        if self.dismounted_this_frame:
            self.dismounted_this_frame = False
            return

        if self.mount_state == MountState.MOUNTED:
            pass
        elif self.mount_state == MountState.DISMOUNTING:
            self.frames_until_dismounted = max(self.frames_until_dismounted - 1, 0)

            if self.frames_until_dismounted == 0:
                self.transition_to_mount_state(MountState.DISMOUNTED, True)
        elif self.mount_state == MountState.DISMOUNTED:
            # TODO check this for each available vehicle, then break on the first one that works
            if self.can_enter_state(MountState.REMOUNTING):
                self.frames_until_remounting = max(self.frames_until_remounting - 1, 0)
            else:
                self.transition_to_mount_state(MountState.DISMOUNTED, True)

            if self.frames_until_remounting == 0:
                self.transition_to_mount_state(MountState.REMOUNTING, True)
        else:
            if self.can_enter_state(MountState.MOUNTED):
                self.frames_until_mounted = max(self.frames_until_mounted - 1, 0)
            else:
                self.transition_to_mount_state(MountState.REMOUNTING, True)

            if self.frames_until_mounted == 0:
                self.transition_to_mount_state(MountState.MOUNTED, True)

    def get_all_points(self) -> list[BasePoint]:
        all_points = []

        for contact_point in self.vehicle.contact_points:
            all_points.append(contact_point.base)

        for contact_point in self.rider.contact_points:
            all_points.append(contact_point.base)

        for flutter_point in self.vehicle.flutter_points:
            all_points.append(flutter_point.base)

        for flutter_point in self.rider.flutter_points:
            all_points.append(flutter_point.base)

        return all_points


def create_default_rider(
    init_state: InitialEntityParams,
    mount_joint_version: RemountVersion,
) -> RiderVehiclePair:
    rider = BaseEntity(init_state["REMOUNT"])
    sled = BaseEntity(init_state["REMOUNT"])
    rider_sled_pair = RiderVehiclePair(rider, sled, mount_joint_version)

    DEFAULT_MOUNT_ENDURANCE = 0.057
    DEFAULT_REPEL_LENGTH_FACTOR = 0.5

    if LR_COM_SCARF:
        SCARF_FRICTION = 0.2
    else:
        SCARF_FRICTION = 0.1

    # Create the contact points first, at their initial positions
    # Order doesn't really matter, added in this order to match linerider.com
    # based test cases
    # Sled points
    PEG = sled.add_contact_point(Vector(0.0, 0.0), 0.8)
    TAIL = sled.add_contact_point(Vector(0.0, 5.0), 0.0)
    NOSE = sled.add_contact_point(Vector(15.0, 5.0), 0.0)
    STRING = sled.add_contact_point(Vector(17.5, 0.0), 0.0)

    # Rider points
    BUTT = rider.add_contact_point(Vector(5.0, 0.0), 0.8)
    SHOULDER = rider.add_contact_point(Vector(5.0, -5.5), 0.8)
    RIGHT_HAND = rider.add_contact_point(Vector(11.5, -5.0), 0.1)
    LEFT_HAND = rider.add_contact_point(Vector(11.5, -5.0), 0.1)
    LEFT_FOOT = rider.add_contact_point(Vector(10.0, 5.0), 0.0)
    RIGHT_FOOT = rider.add_contact_point(Vector(10.0, 5.0), 0.0)
    SCARF_0 = rider.add_flutter_point(Vector(3, -5.5), SCARF_FRICTION)
    SCARF_1 = rider.add_flutter_point(Vector(1, -5.5), SCARF_FRICTION)
    SCARF_2 = rider.add_flutter_point(Vector(-1, -5.5), SCARF_FRICTION)
    SCARF_3 = rider.add_flutter_point(Vector(-3, -5.5), SCARF_FRICTION)
    SCARF_4 = rider.add_flutter_point(Vector(-5, -5.5), SCARF_FRICTION)
    SCARF_5 = rider.add_flutter_point(Vector(-7, -5.5), SCARF_FRICTION)
    SCARF_6 = rider.add_flutter_point(Vector(-9, -5.5), SCARF_FRICTION)

    # Sled bones
    SLED_BACK = sled.add_normal_bone(PEG, TAIL)
    sled.add_normal_bone(TAIL, NOSE)
    sled.add_normal_bone(NOSE, STRING)
    SLED_FRONT = sled.add_normal_bone(STRING, PEG)
    sled.add_normal_bone(PEG, NOSE)
    sled.add_normal_bone(STRING, TAIL)
    rider_sled_pair.add_vehicle_mount_bone(PEG, BUTT, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_vehicle_mount_bone(TAIL, BUTT, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_vehicle_mount_bone(NOSE, BUTT, DEFAULT_MOUNT_ENDURANCE)

    # Rider bones
    TORSO = rider.add_normal_bone(SHOULDER, BUTT)
    rider.add_normal_bone(SHOULDER, LEFT_HAND)
    rider.add_normal_bone(SHOULDER, RIGHT_HAND)
    rider.add_normal_bone(BUTT, LEFT_FOOT)
    rider.add_normal_bone(BUTT, RIGHT_FOOT)
    rider.add_normal_bone(SHOULDER, RIGHT_HAND)
    rider_sled_pair.add_rider_mount_bone(SHOULDER, PEG, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_rider_mount_bone(LEFT_HAND, STRING, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_rider_mount_bone(RIGHT_HAND, STRING, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_rider_mount_bone(LEFT_FOOT, NOSE, DEFAULT_MOUNT_ENDURANCE)
    rider_sled_pair.add_rider_mount_bone(RIGHT_FOOT, NOSE, DEFAULT_MOUNT_ENDURANCE)
    rider.add_repel_bone(SHOULDER, LEFT_FOOT, DEFAULT_REPEL_LENGTH_FACTOR)
    rider.add_repel_bone(SHOULDER, RIGHT_FOOT, DEFAULT_REPEL_LENGTH_FACTOR)
    rider.add_flutter_bone(SHOULDER, SCARF_0)
    rider.add_flutter_bone(SCARF_0, SCARF_1)
    rider.add_flutter_bone(SCARF_1, SCARF_2)
    rider.add_flutter_bone(SCARF_2, SCARF_3)
    rider.add_flutter_bone(SCARF_3, SCARF_4)
    rider.add_flutter_bone(SCARF_4, SCARF_5)
    rider.add_flutter_bone(SCARF_5, SCARF_6)

    # Add the bindings with their joints
    rider_sled_pair.add_joint(TORSO.base, SLED_FRONT.base)
    rider_sled_pair.add_joint(SLED_BACK.base, SLED_FRONT.base)
    sled.add_joint(SLED_BACK.base, SLED_FRONT.base)

    if LRA_LEGACY_FAKIE_CHECK:
        sled.add_joint(TORSO.base, SLED_FRONT.base)

    # Apply initial state once everything is initialized
    # Note that this must be applied after bone rest lengths are calculated
    # because it does not affect bone rest lengths
    rider_sled_pair.apply_initial_state(init_state, TAIL.base.position)

    return rider_sled_pair
