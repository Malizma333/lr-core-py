from engine.grid import Grid
from engine.vector import Vector
from engine.point import BasePoint
from engine.skeleton import Skeleton
from engine.skeleton_mount import SkeletonMount, RemountVersion
from typing import Optional

# TODO: Scrap this and hardcode instead?


# An entity with a skeleton, connected to another entity used for remount processing
# The default self is the vehicle, and the default other is the rider
# The engine's entity array then looks like this [sled1, rider1, sled2, rider2]
# Where sled1.other = rider1 and rider1.other = sled1, and so on
class Entity:
    def __init__(
        self,
        remount_enabled: bool,
        mount_joint_version: RemountVersion,
        skeleton: Skeleton,
    ):
        self.mount_link: Optional[SkeletonMount] = None
        # Constant versioning properties
        self.remount_enabled = remount_enabled
        self.mount_joint_version = mount_joint_version
        self.skeleton = skeleton
        self.physics_processed = False

    def copy(self):
        self.physics_processed = False
        return self

    def get_overall_points(self) -> list[BasePoint]:
        points: list[BasePoint] = []

        for point in self.skeleton.all_points:
            points.append(point)

        if self.other != None:
            for point in self.other.skeleton.all_points:
                points.append(point)

        return points

    def can_remount(self):
        return (
            self.remount_enabled
            and self.skeleton.intact
            and self.mount_phase == MountPhase.DISMOUNTED
        )

    def transition_to_mount_phase(self, new_mount_phase: MountPhase, reset_timer: bool):
        # Sets the new state while safely resetting timers

        self.mount_phase = new_mount_phase

    # Checks if either remounting or mounted states can be entered by checking
    # that the bone stays intact with different strength/endurance remount values
    def can_enter_mount_phase(self, state: MountPhase):
        other = self.require_other()
        remounting = state == MountPhase.REMOUNTING

        for bone in self.skeleton.mount_bones:
            if not bone.get_intact(remounting):
                return False

        for bone in other.skeleton.mount_bones:
            if not bone.get_intact(remounting):
                return False

        for joint in self.skeleton.joints:
            if joint.should_break():
                return False

        for joint in other.skeleton.joints:
            if joint.should_break():
                return False

        for joint in self.skeleton.mount_joints:
            if joint.should_break():
                return False

        return True

    def dismount(self):
        if self.dismounted_this_frame:
            return

        self.dismounted_this_frame = True

        if self.mount_joint_version == RemountVersion.NONE:
            # Just dismount, ignore timers
            self.transition_to_mount_phase(MountPhase.DISMOUNTED, False)
        else:
            if self.mount_phase == MountPhase.MOUNTED:
                # Dismount with timer until next remount
                self.transition_to_mount_phase(MountPhase.DISMOUNTING, True)
            elif self.mount_phase == MountPhase.REMOUNTING:
                # Revert from remounting to dismounted without timer
                self.transition_to_mount_phase(MountPhase.DISMOUNTED, True)

        other = self.require_other()
        other.dismount()

    def process(self, gravity: Vector, grid: Grid):
        if self.physics_processed:
            return

        if self.other != None:
            self.skeleton.process(self.other.skeleton, gravity, grid)
        else:
            self.skeleton.process(None, gravity, grid)

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
                self.transition_to_mount_phase(MountPhase.DISMOUNTED, True)
        elif self.mount_phase == MountPhase.DISMOUNTED:
            # TODO check this for each available vehicle, then break on the first one that works
            return
            if self.can_enter_mount_phase(MountPhase.REMOUNTING):
                self.frames_until_can_remount = max(
                    self.frames_until_can_remount - 1, 0
                )
            else:
                self.transition_to_mount_phase(MountPhase.DISMOUNTED, True)

            if self.frames_until_can_remount == 0:
                self.transition_to_mount_phase(MountPhase.REMOUNTING, True)
        else:
            return
            if self.can_enter_mount_phase(MountPhase.MOUNTED):
                self.frames_until_mounted = max(self.frames_until_mounted - 1, 0)
            else:
                self.transition_to_mount_phase(MountPhase.REMOUNTING, True)

            if self.frames_until_mounted == 0:
                self.transition_to_mount_phase(MountPhase.MOUNTED, True)
