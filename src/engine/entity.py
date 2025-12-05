from engine.grid import Grid
from engine.vector import Vector
from engine.point import ContactPoint, FlutterPoint, BasePoint
from engine.bone import NormalBone, RepelBone, MountBone, FlutterBone, BaseBone
from engine.joint import Joint
from engine.flags import LR_COM_SCARF, OFFSET_BEFORE_BONES
from enum import Enum
from typing import Union, TypedDict
import math


class InitialEntityParams(TypedDict):
    POSITION: Vector
    VELOCITY: Vector
    ROTATION: float  # In degrees
    CAN_REMOUNT: bool


class MountPhase(Enum):
    # Connected to another entity
    MOUNTED = 0
    # Just disconnected, not yet ready to reconnect
    DISMOUNTING = 1
    # Fully disconnected, ready to reconnect
    DISMOUNTED = 2
    # Currently reconnecting
    REMOUNTING = 3


class RemountVersion(Enum):
    # pre-remount (indicated with "remountable": undefined) the tail fakie breaks the sled after dismount
    NONE = 0
    # remount-v1 (indicated with "remountable": true) the tail fakie does not break the sled after dismount (bug)
    COM_V1 = 1
    # remount-v2 (indicated with "remountable": 1) the tail fakie breaks the sled after dismount (fixed)
    COM_V2 = 2
    # lra implements its own version of remounting
    LRA = 3


# Keeps track of entity state (mostly remounting checks)
class EntityState:
    def __init__(
        self,
        init_state: InitialEntityParams,
        remount_version: RemountVersion,
    ):
        self.init_state = init_state
        self.remount_version = remount_version
        # This should be per-skeleton but for now hardcoded for overall entity
        self.sled_intact = True
        self.mount_phase = MountPhase.MOUNTED
        self.frames_until_dismounted = 0
        self.frames_until_remounting = 0
        self.frames_until_mounted = 0

    def sled_is_intact(self):
        return self.sled_intact

    def break_sled(self):
        self.sled_intact = False

    def is_mounted(self):
        return self.mount_phase in (MountPhase.MOUNTED, MountPhase.REMOUNTING)

    def available_to_swap_sled(self):
        return self.sled_intact and not self.is_mounted()

    def can_enter_remounting(self, entity: "Entity", other_entities: list["Entity"]):
        for other_entity in other_entities:
            if not other_entity.state.available_to_swap_sled():
                continue

            # Swap sleds to check entity can safely remount
            entity.swap_sleds(other_entity)

            if self.can_enter_mount_phase(entity, MountPhase.REMOUNTING):
                return True

            # Swap sleds back if we failed
            entity.swap_sleds(other_entity)

        return False

    # Checks if either remounting or mounted states can be entered by checking
    # that the bone stays intact with different strength/endurance remount values
    def can_enter_mount_phase(self, entity: "Entity", mount_phase: MountPhase):
        for bone in entity.structural_bones:
            if isinstance(bone, MountBone):
                if not bone.get_intact(mount_phase == MountPhase.REMOUNTING):
                    return False

        if self.remount_version != RemountVersion.LRA:
            for joint in entity.break_joints:
                if joint.should_break():
                    return False

            for joint in entity.mount_joints:
                if joint.should_break():
                    return False

        return True

    def enter_mount_phase(self, new_mount_state: MountPhase, reset_timer: bool):
        # Sets the new state while safely resetting timers
        if new_mount_state == MountPhase.DISMOUNTING and reset_timer:
            self.frames_until_dismounted = 30
        elif new_mount_state == MountPhase.DISMOUNTED and reset_timer:
            self.frames_until_remounting = 3
        elif new_mount_state == MountPhase.REMOUNTING and reset_timer:
            self.frames_until_mounted = 3

        self.mount_phase = new_mount_state

    def dismount(self):
        if (
            self.remount_version == RemountVersion.NONE
            or not self.init_state["CAN_REMOUNT"]
        ):
            # Just dismount, ignore timers
            self.enter_mount_phase(MountPhase.DISMOUNTED, False)
        else:
            if self.mount_phase == MountPhase.MOUNTED:
                # Dismount with timer until next remount
                self.enter_mount_phase(MountPhase.DISMOUNTING, True)
            elif self.mount_phase == MountPhase.REMOUNTING:
                # Revert from remounting to dismounted without timer
                self.enter_mount_phase(MountPhase.DISMOUNTED, True)

    def copy(self):
        new_state = EntityState(self.init_state, self.remount_version)
        new_state.sled_intact = self.sled_intact
        new_state.mount_phase = self.mount_phase
        new_state.frames_until_dismounted = self.frames_until_dismounted
        new_state.frames_until_remounting = self.frames_until_remounting
        new_state.frames_until_mounted = self.frames_until_mounted
        return new_state


# A hardcoded entity implementation for just the default rider and sled
# A proper implementation adding support for custom skeletons would likely
# separate the rider and sled as general skeleton entities and add a general
# connection class for how to connect those skeleton entities with mount bones
# and mount joints
class Entity:
    def __init__(self, state: EntityState):
        self.state = state
        self.contact_points: list[ContactPoint] = []
        self.flutter_points: list[FlutterPoint] = []
        self.points: list[BasePoint] = []
        self.structural_bones: list[Union[NormalBone, MountBone, RepelBone]] = []
        self.flutter_bones: list[FlutterBone] = []
        self.bones: list[BaseBone] = []
        self.break_joints: list[Joint] = []
        self.mount_joints: list[Joint] = []

        MOUNT_ENDURANCE = 0.057
        REPEL_LENGTH_FACTOR = 0.5
        SCARF_FRICTION = 0.1
        if LR_COM_SCARF:
            SCARF_FRICTION = 0.2

        # Create the contact points first, at their initial positions
        # Order doesn't really matter, added in this order to match linerider.com
        # based test cases (and because hard-coded parts depend on it)

        # Sled points
        PEG = self.add_contact_point(Vector(0.0, 0.0), 0.8)
        TAIL = self.add_contact_point(Vector(0.0, 5.0), 0.0)
        NOSE = self.add_contact_point(Vector(15.0, 5.0), 0.0)
        STRING = self.add_contact_point(Vector(17.5, 0.0), 0.0)

        # Rider points
        BUTT = self.add_contact_point(Vector(5.0, 0.0), 0.8)
        SHOULDER = self.add_contact_point(Vector(5.0, -5.5), 0.8)
        RIGHT_HAND = self.add_contact_point(Vector(11.5, -5.0), 0.1)
        LEFT_HAND = self.add_contact_point(Vector(11.5, -5.0), 0.1)
        LEFT_FOOT = self.add_contact_point(Vector(10.0, 5.0), 0.0)
        RIGHT_FOOT = self.add_contact_point(Vector(10.0, 5.0), 0.0)
        SCARF_0 = self.add_flutter_point(Vector(3, -5.5), SCARF_FRICTION)
        SCARF_1 = self.add_flutter_point(Vector(1, -5.5), SCARF_FRICTION)
        SCARF_2 = self.add_flutter_point(Vector(-1, -5.5), SCARF_FRICTION)
        SCARF_3 = self.add_flutter_point(Vector(-3, -5.5), SCARF_FRICTION)
        SCARF_4 = self.add_flutter_point(Vector(-5, -5.5), SCARF_FRICTION)
        SCARF_5 = self.add_flutter_point(Vector(-7, -5.5), SCARF_FRICTION)
        SCARF_6 = self.add_flutter_point(Vector(-9, -5.5), SCARF_FRICTION)

        if OFFSET_BEFORE_BONES:
            self.apply_initial_state()

        # Sled bones
        SLED_BACK = self.add_normal_bone(PEG, TAIL)
        self.add_normal_bone(TAIL, NOSE)
        self.add_normal_bone(NOSE, STRING)
        SLED_FRONT = self.add_normal_bone(STRING, PEG)
        self.add_normal_bone(PEG, NOSE)
        self.add_normal_bone(STRING, TAIL)
        self.add_mount_bone(PEG, BUTT, MOUNT_ENDURANCE)
        self.add_mount_bone(TAIL, BUTT, MOUNT_ENDURANCE)
        self.add_mount_bone(NOSE, BUTT, MOUNT_ENDURANCE)

        # Rider bones
        TORSO = self.add_normal_bone(SHOULDER, BUTT)
        self.add_normal_bone(SHOULDER, LEFT_HAND)
        self.add_normal_bone(SHOULDER, RIGHT_HAND)
        self.add_normal_bone(BUTT, LEFT_FOOT)
        self.add_normal_bone(BUTT, RIGHT_FOOT)
        self.add_normal_bone(SHOULDER, RIGHT_HAND)
        self.add_mount_bone(SHOULDER, PEG, MOUNT_ENDURANCE)
        self.add_mount_bone(LEFT_HAND, STRING, MOUNT_ENDURANCE)
        self.add_mount_bone(RIGHT_HAND, STRING, MOUNT_ENDURANCE)
        self.add_mount_bone(LEFT_FOOT, NOSE, MOUNT_ENDURANCE)
        self.add_mount_bone(RIGHT_FOOT, NOSE, MOUNT_ENDURANCE)
        self.add_repel_bone(SHOULDER, LEFT_FOOT, REPEL_LENGTH_FACTOR)
        self.add_repel_bone(SHOULDER, RIGHT_FOOT, REPEL_LENGTH_FACTOR)
        self.add_flutter_bone(SHOULDER, SCARF_0)
        self.add_flutter_bone(SCARF_0, SCARF_1)
        self.add_flutter_bone(SCARF_1, SCARF_2)
        self.add_flutter_bone(SCARF_2, SCARF_3)
        self.add_flutter_bone(SCARF_3, SCARF_4)
        self.add_flutter_bone(SCARF_4, SCARF_5)
        self.add_flutter_bone(SCARF_5, SCARF_6)

        if not OFFSET_BEFORE_BONES:
            self.apply_initial_state()

        # Add the bindings with their joints
        self.add_mount_joint(SLED_BACK, SLED_FRONT)
        self.add_mount_joint(TORSO, SLED_FRONT)
        self.add_break_joint(SLED_BACK, SLED_FRONT)

        # Variable scoped to this class for checking dismount during this frame
        self.dismounted_this_frame = False

    def apply_initial_state(self):
        # This updates the contact points with initial position, velocity, and initial rotation
        # Note that the use of cos and sin here may not give the same results for all numbers in different languages
        # This gets tested with 50 degrees so it happens to pass the test case
        cos_theta = math.cos(self.state.init_state["ROTATION"] * math.pi / 180)
        sin_theta = math.sin(self.state.init_state["ROTATION"] * math.pi / 180)
        origin = self.contact_points[1].base.position  # Hardcoded to be tail

        for point in self.points:
            offset = point.position - origin
            point.update_state(
                Vector(
                    origin.x + offset.x * cos_theta - offset.y * sin_theta,
                    origin.y + offset.x * sin_theta + offset.y * cos_theta,
                ),
                point.velocity,
                point.previous_position,
            )

        for point in self.points:
            start_position = point.position + self.state.init_state["POSITION"]
            start_velocity = point.velocity + self.state.init_state["VELOCITY"]
            point.update_state(
                start_position, start_velocity, start_position - start_velocity
            )

    def copy(self):
        new_entity = Entity(self.state.copy())

        for i in range(len(self.points)):
            new_entity.points[i].copy(self.points[i])

        return new_entity

    # Hard coded function to swap sleds between two entities
    # Full implementation should have a proper mount bone connection system
    # (likely with a template class that defines how two skeletons mount each other)
    def swap_sleds(self, other: "Entity"):
        SLED_POINTS = (0, 1, 2, 3)
        if self.state.remount_version == RemountVersion.COM_V2:
            sled_intact = self.state.sled_intact
            self.state.sled_intact = other.state.sled_intact
            other.state.sled_intact = sled_intact
        for i in SLED_POINTS:
            point = BasePoint(
                self.points[i].position,
                self.points[i].velocity,
                self.points[i].previous_position,
            )
            self.points[i].copy(other.points[i])
            other.points[i].copy(point)

    def add_contact_point(self, start_position: Vector, friction: float):
        point = ContactPoint(start_position, friction)
        self.points.append(point.base)
        self.contact_points.append(point)
        return len(self.points) - 1

    def add_flutter_point(self, start_position: Vector, air_friction: float):
        point = FlutterPoint(start_position, air_friction)
        self.points.append(point.base)
        self.flutter_points.append(point)
        return len(self.points) - 1

    def add_normal_bone(self, point1: int, point2: int):
        bone = NormalBone(self.points[point1], self.points[point2])
        self.bones.append(bone.base)
        self.structural_bones.append(bone)
        return len(self.bones) - 1

    def add_mount_bone(self, point1: int, point2: int, endurance: float):
        bone = MountBone(self.points[point1], self.points[point2], endurance)
        self.bones.append(bone.base)
        self.structural_bones.append(bone)
        return len(self.bones) - 1

    def add_repel_bone(self, point1: int, point2: int, length_factor: float):
        bone = RepelBone(self.points[point1], self.points[point2], length_factor)
        self.bones.append(bone.base)
        self.structural_bones.append(bone)
        return len(self.bones) - 1

    def add_flutter_bone(self, point1: int, point2: int):
        bone = FlutterBone(self.points[point1], self.points[point2])
        self.bones.append(bone.base)
        self.flutter_bones.append(bone)
        return len(self.bones) - 1

    def add_break_joint(self, bone1: int, bone2: int):
        joint = Joint(self.bones[bone1], self.bones[bone2])
        self.break_joints.append(joint)

    def add_mount_joint(self, bone1: int, bone2: int):
        joint = Joint(self.bones[bone1], self.bones[bone2])
        self.mount_joints.append(joint)

    def process_initial_points(self, gravity: Vector):
        for point in self.contact_points:
            point.initial_step(gravity)

        for point in self.flutter_points:
            point.initial_step(gravity)

    def process_bones(self, initial_phase: MountPhase):
        REMOUNT_STRENGTH_FACTOR = 0.1
        LRA_REMOUNT_STRENGTH_FACTOR = 0.5

        for bone in self.structural_bones:
            if isinstance(bone, NormalBone) or isinstance(bone, RepelBone):
                if (
                    self.state.remount_version == RemountVersion.LRA
                    and initial_phase == MountPhase.REMOUNTING
                ):
                    # Non-mount bones are affected by strength multiplier in LRA remounting
                    strength = LRA_REMOUNT_STRENGTH_FACTOR
                else:
                    strength = 1

                bone.process(strength)
            else:
                if (
                    self.state.remount_version == RemountVersion.LRA
                    and (
                        initial_phase == MountPhase.MOUNTED
                        or initial_phase == MountPhase.REMOUNTING
                    )
                ) or (
                    self.state.remount_version != RemountVersion.LRA
                    and self.state.is_mounted()
                ):
                    # LRA uses the mount phase known at the start of this frame,
                    # while .com uses the current mount phase (which can change)
                    if (
                        self.state.remount_version == RemountVersion.LRA
                        and initial_phase == MountPhase.REMOUNTING
                    ):
                        intact = bone.get_intact(True)
                        strength = LRA_REMOUNT_STRENGTH_FACTOR
                    elif (
                        self.state.remount_version != RemountVersion.LRA
                        and self.state.mount_phase == MountPhase.REMOUNTING
                    ):
                        intact = bone.get_intact(True)
                        strength = REMOUNT_STRENGTH_FACTOR
                    else:
                        intact = bone.get_intact(False)
                        strength = 1

                    if not self.dismounted_this_frame:
                        if intact:
                            bone.process(strength)
                        else:
                            self.dismounted_this_frame = True
                            self.state.dismount()

    def process_collisions(self, grid: Grid):
        for point in self.contact_points:
            interacting_lines = grid.get_lines_near_position(point.base.position)
            for line in interacting_lines:
                new_pos, new_prev_pos = line.interact(point)
                point.base.update_state(new_pos, point.base.velocity, new_prev_pos)

    def process_flutter_bones(self):
        for bone in self.flutter_bones:
            bone.process()

    def process_mount_joints(self):
        if not self.state.is_mounted():
            return

        for joint in self.mount_joints:
            if joint.should_break() and not self.dismounted_this_frame:
                self.dismounted_this_frame = True
                self.state.dismount()
                if self.state.remount_version == RemountVersion.LRA:
                    # LRA also breaks sled on mount joint break
                    self.state.break_sled()

    def process_break_joints(self):
        if (
            self.state.remount_version == RemountVersion.LRA
            or self.state.remount_version == RemountVersion.COM_V1
        ):
            # Don't process joints if dismounted
            if not self.state.is_mounted():
                return

        for joint in self.break_joints:
            if self.state.sled_is_intact() and joint.should_break():
                self.state.break_sled()

    def process_skeleton(self, gravity: Vector, grid: Grid):
        # momentum
        self.process_initial_points(gravity)

        initial_phase = self.state.mount_phase
        for _ in range(6):
            # bones
            self.process_bones(initial_phase)
            # line collisions
            self.process_collisions(grid)

        # flutter bones (like scarf)
        self.process_flutter_bones()

        # check dismount
        self.process_mount_joints()

        # check skeleton break (like sled break)
        self.process_break_joints()

    def process_remount(self, other_entities: list["Entity"]):
        if (
            self.state.remount_version == RemountVersion.NONE
            or self.state.init_state["CAN_REMOUNT"] == False
        ):
            return

        if self.dismounted_this_frame:
            self.dismounted_this_frame = False
            return

        if self.state.remount_version == RemountVersion.LRA:
            if not self.state.sled_intact:
                self.state.enter_mount_phase(MountPhase.DISMOUNTED, False)
                return

            if self.state.mount_phase == MountPhase.MOUNTED:
                pass
            elif self.state.mount_phase == MountPhase.DISMOUNTING:
                if self.state.frames_until_dismounted <= 0:
                    self.state.enter_mount_phase(MountPhase.DISMOUNTED, True)
                else:
                    self.state.frames_until_dismounted -= 1
            elif self.state.mount_phase == MountPhase.DISMOUNTED:
                if self.state.can_enter_remounting(self, other_entities):
                    if self.state.frames_until_remounting <= 0:
                        self.state.enter_mount_phase(MountPhase.REMOUNTING, True)
                    else:
                        self.state.frames_until_remounting -= 1
                else:
                    self.state.enter_mount_phase(MountPhase.DISMOUNTED, True)
            else:
                if self.state.can_enter_mount_phase(self, MountPhase.MOUNTED):
                    if self.state.frames_until_mounted <= 0:
                        self.state.enter_mount_phase(MountPhase.MOUNTED, True)
                    else:
                        self.state.frames_until_mounted -= 1
                else:
                    self.state.enter_mount_phase(MountPhase.REMOUNTING, True)
        else:
            if self.state.mount_phase == MountPhase.MOUNTED:
                pass
            elif self.state.mount_phase == MountPhase.DISMOUNTING:
                self.state.frames_until_dismounted -= 1
                if self.state.frames_until_dismounted <= 0:
                    self.state.enter_mount_phase(MountPhase.DISMOUNTED, True)
            elif self.state.mount_phase == MountPhase.DISMOUNTED:
                if self.state.can_enter_remounting(self, other_entities):
                    self.state.frames_until_remounting -= 1
                else:
                    self.state.enter_mount_phase(MountPhase.DISMOUNTED, True)
                if self.state.frames_until_remounting <= 0:
                    self.state.enter_mount_phase(MountPhase.REMOUNTING, True)
            else:
                if self.state.can_enter_mount_phase(self, MountPhase.MOUNTED):
                    self.state.frames_until_mounted -= 1
                else:
                    self.state.enter_mount_phase(MountPhase.REMOUNTING, True)
                if self.state.frames_until_mounted <= 0:
                    self.state.enter_mount_phase(MountPhase.MOUNTED, True)
