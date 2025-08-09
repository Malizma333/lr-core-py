from engine.skeleton import Skeleton
from enum import Enum


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


class SkeletonMount:
    def __init__(
        self, skeletons: tuple[Skeleton, Skeleton], remount_version: RemountVersion
    ):
        self.skeletons = skeletons
        self.remount_version = remount_version
        self.mount_phase = MountPhase.MOUNTED
        self.frames_until_dismounted = 0
        self.frames_until_can_remount = 0
        self.frames_until_mounted = 0

    def is_mounted(self):
        return (
            self.mount_phase == MountPhase.MOUNTED
            or self.mount_phase == MountPhase.REMOUNTING
        )

    def process(self):
        if self.mount_phase == MountPhase.MOUNTED:
            if not self.both_mount_bones_intact():
                self.transition(MountPhase.DISMOUNTING)

        elif self.mount_phase == MountPhase.DISMOUNTING:
            self.frames_until_dismounted -= 1
            if self.frames_until_dismounted <= 0:
                self.transition(MountPhase.DISMOUNTED)

        elif self.mount_phase == MountPhase.DISMOUNTED:
            if self.can_remount():
                self.frames_until_can_remount -= 1
                if self.frames_until_can_remount <= 0:
                    self.transition(MountPhase.REMOUNTING)

        elif self.mount_phase == MountPhase.REMOUNTING:
            if self.both_mount_bones_intact():
                self.frames_until_mounted -= 1
                if self.frames_until_mounted <= 0:
                    self.transition(MountPhase.MOUNTED)

    def both_mount_bones_intact(self):
        return self.skeletons[0].mount_bones_intact(
            remounting=self.mount_phase == MountPhase.REMOUNTING
        ) and self.skeletons[1].mount_bones_intact(
            remounting=self.mount_phase == MountPhase.REMOUNTING
        )

    def can_remount(self):
        # check both skeletons’ joints and mount joints
        return (
            self.both_mount_bones_intact()
            and self.skeletons[0].joints_intact()
            and self.skeletons[1].joints_intact()
        )

    def transition(self, new_mount_phase: MountPhase, reset_timer: bool):
        if new_mount_phase == MountPhase.DISMOUNTING and reset_timer:
            self.frames_until_dismounted = 30
        elif new_mount_phase == MountPhase.DISMOUNTED and reset_timer:
            self.frames_until_can_remount = 3
        elif new_mount_phase == MountPhase.REMOUNTING and reset_timer:
            self.frames_until_mounted = 3
        # handle timers here
        self.mount_phase = new_mount_phase
