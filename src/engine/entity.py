from engine.grid import Grid
from engine.vector import Vector
from engine.point import BasePoint, ContactPoint, FlutterPoint
from engine.bone import NormalBone, RepelBone, MountBone, FlutterBone, BaseBone
from engine.joint import Joint
from engine.flags import LRA_LEGACY_FAKIE_CHECK
from enum import Enum
from typing import Optional


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


# An entity with a skeleton, connected to another entity used for remount processing
# The default self is the vehicle, and the default other is the rider
# The engine's entity array then looks like this [sled1, rider1, sled2, rider2]
# Where sled1.other = rider1 and rider1.other = sled1, and so on
class Entity:
    def __init__(self, remount_enabled: bool, mount_joint_version: RemountVersion):
        # Constant versioning properties
        self.remount_enabled = remount_enabled
        self.mount_joint_version = mount_joint_version
        # Entity points that define the skeleton
        self.contact_points: list[ContactPoint] = []
        self.flutter_points: list[FlutterPoint] = []
        # Bones connecting points that adjust point positions
        self.normal_bones: list[NormalBone] = []
        self.mount_bones: list[MountBone] = []
        self.repel_bones: list[RepelBone] = []
        self.flutter_bones: list[FlutterBone] = []
        self.all_bones: list[BaseBone] = []
        # Joints that change state whenever bones cross
        self.joints: list[Joint] = []
        self.mount_joints: list[Joint] = []
        # Entity state
        self.intact = True
        self.physics_processed = False
        self.other: Optional[Entity] = None
        self.mount_phase = MountPhase.MOUNTED
        self.frames_until_dismounted = 0
        self.frames_until_remounting = 0
        self.frames_until_mounted = 0
        self.dismounted_this_frame = False

    def copy(self):
        self.physics_processed = False
        return self

    # Ensures other entity exists before using it
    def require_other(self):
        if self.other == None:
            raise Exception("Other undefined")
        return self.other

    def get_overall_points(self) -> list[BasePoint]:
        points: list[BasePoint] = []

        for point in self.contact_points:
            points.append(point.base)

        for point in self.flutter_points:
            points.append(point.base)

        if self.other != None:
            for point in self.other.contact_points:
                points.append(point.base)

            for point in self.other.flutter_points:
                points.append(point.base)

        return points

    def can_remount(self):
        return (
            self.remount_enabled
            and self.intact
            and self.mount_phase == MountPhase.DISMOUNTED
        )

    def mount(self, other: "Entity"):
        self.other = other
        other.other = self

    def is_mounted(self):
        return (
            self.mount_phase == MountPhase.MOUNTED
            or self.mount_phase == MountPhase.REMOUNTING
        )

    def transition_to_mount_state(self, new_mount_state: MountPhase, reset_timer: bool):
        # Sets the new state while safely resetting timers
        if new_mount_state == MountPhase.DISMOUNTING and reset_timer:
            self.frames_until_dismounted = 30
        elif new_mount_state == MountPhase.DISMOUNTED and reset_timer:
            self.frames_until_remounting = 3
        elif new_mount_state == MountPhase.REMOUNTING and reset_timer:
            self.frames_until_mounted = 3

        self.mount_phase = new_mount_state

    # Checks if either remounting or mounted states can be entered by checking
    # that the bone stays intact with different strength/endurance remount values
    def can_enter_mount_state(self, state: MountPhase):
        other = self.require_other()
        remounting = state == MountPhase.REMOUNTING

        for bone in self.mount_bones:
            if not bone.get_intact(remounting):
                return False

        for bone in other.mount_bones:
            if not bone.get_intact(remounting):
                return False

        for joint in self.joints:
            if joint.should_break():
                return False

        for joint in other.joints:
            if joint.should_break():
                return False

        for joint in self.mount_joints:
            if joint.should_break():
                return False

        return True

    def dismount(self):
        if self.dismounted_this_frame:
            return

        self.dismounted_this_frame = True

        if self.mount_joint_version == RemountVersion.NONE:
            # Just dismount, ignore timers
            self.transition_to_mount_state(MountPhase.DISMOUNTED, False)
        else:
            if self.mount_phase == MountPhase.MOUNTED:
                # Dismount with timer until next remount
                self.transition_to_mount_state(MountPhase.DISMOUNTING, True)
            elif self.mount_phase == MountPhase.REMOUNTING:
                # Revert from remounting to dismounted without timer
                self.transition_to_mount_state(MountPhase.DISMOUNTED, True)

        other = self.require_other()
        other.dismount()

    def add_contact_point(self, position: Vector, friction: float) -> int:
        base_point = BasePoint(position, Vector(0, 0), position)
        point = ContactPoint(base_point, friction)
        self.contact_points.append(point)
        return len(self.contact_points) - 1

    def add_flutter_point(self, position: Vector, air_friction: float) -> int:
        base_point = BasePoint(position, Vector(0, 0), position)
        point = FlutterPoint(base_point, air_friction)
        self.flutter_points.append(point)
        return len(self.flutter_points) - 1

    def add_normal_bone(self, point1_id: int, point2_id: int) -> int:
        bone = NormalBone(
            self.contact_points[point1_id].base, self.contact_points[point2_id].base
        )
        self.normal_bones.append(bone)
        self.all_bones.append(bone.base)
        return len(self.all_bones) - 1

    def add_mount_bone(self, point1_id: int, point2_id: int, endurance: float) -> int:
        if self.other == None:
            return -1

        bone = MountBone(
            self.contact_points[point1_id].base,
            self.other.contact_points[point2_id].base,
            endurance,
        )
        self.mount_bones.append(bone)
        self.all_bones.append(bone.base)
        return len(self.all_bones) - 1

    def add_repel_bone(self, point1: int, point2: int, length_factor: float) -> int:
        bone = RepelBone(
            self.contact_points[point1].base,
            self.contact_points[point2].base,
            length_factor,
        )
        self.repel_bones.append(bone)
        self.all_bones.append(bone.base)
        return len(self.all_bones) - 1

    def add_flutter_bone(self, point1: int, point2: int) -> int:
        bone = FlutterBone(
            self.flutter_points[point1].base, self.flutter_points[point2].base
        )
        self.flutter_bones.append(bone)
        self.all_bones.append(bone.base)
        return len(self.all_bones) - 1

    def add_flutter_connector_bone(self, point1: int, point2: int) -> int:
        bone = FlutterBone(
            self.contact_points[point1].base, self.flutter_points[point2].base
        )
        self.flutter_bones.append(bone)
        self.all_bones.append(bone.base)
        return len(self.all_bones) - 1

    # Adds a joint between two bones on this entity
    # The joint sets this entity's intact state
    def add_self_joint(self, bone1: int, bone2: int):
        self.joints.append(Joint(self.all_bones[bone1], self.all_bones[bone2]))

    # Adds a joint between a bone on this entity and the other entity
    # The joint sets this entity's intact state
    def add_other_joint(self, bone1: int, bone2: int):
        other = self.require_other()
        self.joints.append(Joint(self.all_bones[bone1], other.all_bones[bone2]))

    # Adds a joint between two bones on this entity
    # The joint sets this entity's mount state
    def add_self_mount_joint(self, bone1: int, bone2: int):
        self.mount_joints.append(Joint(self.all_bones[bone1], self.all_bones[bone2]))

    # Adds a joint between a bone on this entity and the other entity
    # The joint sets this entity's mount state
    def add_other_mount_joint(self, bone1: int, bone2: int):
        other = self.require_other()
        self.mount_joints.append(Joint(self.all_bones[bone1], other.all_bones[bone2]))

    def process_initial_points(self, gravity: Vector):
        for point in self.contact_points:
            point.initial_step(gravity)

        for point in self.flutter_points:
            point.initial_step(gravity)

    def process_structural_bones(self):
        for bone in self.normal_bones:
            bone.process()

        for bone in self.mount_bones:
            if self.is_mounted():
                remounting = self.mount_phase == MountPhase.REMOUNTING
                intact = bone.get_intact(remounting)
                bone.process(remounting)

                if not intact:
                    self.dismount()

        for bone in self.repel_bones:
            bone.process()

    def process_collisions(self, grid: Grid):
        for point in self.contact_points:
            interacting_lines = grid.get_interacting_lines(point)
            for line in interacting_lines:
                new_pos, new_prev_pos = line.interact(point)
                point.base.update_state(new_pos, point.base.velocity, new_prev_pos)

    def process_flutter_bones(self):
        for bone in self.flutter_bones:
            bone.process()

    def process_joints(self):
        if LRA_LEGACY_FAKIE_CHECK:
            # Don't process joints if dismounted
            if not self.is_mounted():
                return

        self.process_mount_joints()

        if self.mount_joint_version == RemountVersion.COM_V1:
            # Don't process self joints afterward if dismounted
            if self.is_mounted():
                self.process_self_joints()
        else:
            # Process self joints regardless
            self.process_self_joints()

        if self.other != None:
            self.other.process_self_joints()

    def process_mount_joints(self):
        if self.other == None:
            return

        for joint in self.mount_joints:
            if self.is_mounted() and joint.should_break():
                self.dismount()

        for joint in self.other.mount_joints:
            if self.other.is_mounted() and joint.should_break():
                self.other.dismount()

    def process_self_joints(self):
        for joint in self.joints:
            if self.intact and joint.should_break():
                self.intact = False

    def process_skeleton(self, gravity: Vector, grid: Grid):
        if self.physics_processed:
            return

        # momentum
        self.process_initial_points(gravity)
        if self.other != None:
            self.other.process_initial_points(gravity)

        for _ in range(6):
            # bones
            self.process_structural_bones()
            if self.other != None:
                self.other.process_structural_bones()

            # line collisions
            self.process_collisions(grid)
            if self.other != None:
                self.other.process_collisions(grid)

        # flutter bones (like scarf)
        self.process_flutter_bones()
        if self.other != None:
            self.other.process_flutter_bones()

        # dismount or break entities (like sled break)
        self.process_joints()

        self.physics_processed = True
        if self.other != None:
            self.other.physics_processed = True

    def process_remount(self):
        if (
            self.mount_joint_version == RemountVersion.NONE
            or self.remount_enabled == False
        ):
            return

        if self.dismounted_this_frame:
            self.other = None
            self.dismounted_this_frame = False
            return

        if self.mount_phase == MountPhase.MOUNTED:
            pass
        elif self.mount_phase == MountPhase.DISMOUNTING:
            self.frames_until_dismounted = max(self.frames_until_dismounted - 1, 0)

            if self.frames_until_dismounted == 0:
                self.transition_to_mount_state(MountPhase.DISMOUNTED, True)
        elif self.mount_phase == MountPhase.DISMOUNTED:
            # TODO check this for each available vehicle, then break on the first one that works
            return
            if self.can_enter_mount_state(MountPhase.REMOUNTING):
                self.frames_until_remounting = max(self.frames_until_remounting - 1, 0)
            else:
                self.transition_to_mount_state(MountPhase.DISMOUNTED, True)

            if self.frames_until_remounting == 0:
                self.transition_to_mount_state(MountPhase.REMOUNTING, True)
        else:
            return
            if self.can_enter_mount_state(MountPhase.MOUNTED):
                self.frames_until_mounted = max(self.frames_until_mounted - 1, 0)
            else:
                self.transition_to_mount_state(MountPhase.REMOUNTING, True)

            if self.frames_until_mounted == 0:
                self.transition_to_mount_state(MountPhase.MOUNTED, True)
