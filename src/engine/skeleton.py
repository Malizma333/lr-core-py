from engine.bone import NormalBone, RepelBone, FlutterBone, MountBone, BaseBone
from engine.point import ContactPoint, FlutterPoint, BasePoint
from engine.joint import Joint
from engine.vector import Vector
from engine.grid import Grid
from engine.flags import LRA_LEGACY_FAKIE_CHECK
from typing import Optional


# A template bone structure describing how to create some skeleton type
class SkeletonTemplate:
    def __init__(self):
        self.points: list[BasePoint] = []
        self.contact_points: dict[int, ContactPoint] = {}
        self.flutter_points: dict[int, FlutterPoint] = {}
        self.bone_point_indices: list[tuple[int, int]] = []
        self.bones: list[BaseBone] = []
        self.normal_bones: dict[int, NormalBone] = {}
        self.mount_bones: dict[int, MountBone] = {}
        self.repel_bones: dict[int, RepelBone] = {}
        self.flutter_bones: dict[int, FlutterBone] = {}
        self.joint_bone_indices: list[tuple[int, int]] = []
        self.joints: dict[int, Joint] = {}
        self.mount_joints: dict[int, Joint] = {}

    def register_contact_point(self, position: Vector, friction: float) -> int:
        point = BasePoint(position, Vector(0, 0), position)
        self.points.append(point)
        i = len(self.points) - 1
        self.contact_points[i] = ContactPoint(point, friction)
        return i

    def create_contact_points(self):
        points: dict[int, ContactPoint] = {}
        for i, point in self.contact_points.items():
            points[i] = point.copy()
        return points

    def register_flutter_point(self, position: Vector, air_friction: float) -> int:
        point = BasePoint(position, Vector(0, 0), position)
        self.points.append(point)
        i = len(self.points) - 1
        self.flutter_points[i] = FlutterPoint(point, air_friction)
        return i

    def create_flutter_points(self):
        points: dict[int, FlutterPoint] = {}
        for i, point in self.flutter_points.items():
            points[i] = point.copy()
        return points

    def generate_all_points(
        self,
        contact_points: dict[int, ContactPoint],
        flutter_points: dict[int, FlutterPoint],
    ):
        points: dict[int, BasePoint] = {}
        for i, point in contact_points.items():
            points[i] = point.base
        for i, point in flutter_points.items():
            points[i] = point.base
        return points

    def register_normal_bone(self, points: tuple[int, int]) -> int:
        bone = NormalBone(self.points[points[0]], self.points[points[1]])
        self.bone_point_indices.append(points)
        i = len(self.bone_point_indices) - 1
        self.normal_bones[i] = bone
        self.bones.append(bone.base)
        return i

    def generate_normal_bones(self, created_points: dict[int, BasePoint]):
        bones: dict[int, NormalBone] = {}
        for i, bone in self.normal_bones.items():
            point_indices = self.bone_point_indices[i]
            bones[i] = bone.copy(
                created_points[point_indices[0]],
                created_points[point_indices[1]],
            )
        return bones

    #     def register_mount_bone(self, points: tuple[int, int], endurance: float) -> int:
    #         bone = MountBone(self.points[points[0]], self.points[points[1]], endurance)
    #         self.bone_point_indices.append(points)
    #         i = len(self.bone_point_indices) - 1
    #         self.mount_bones[i] = bone
    #         self.bones.append(bone.base)
    #         return i
    #
    #     def generate_mount_bones(
    #         self, created_points: list[BasePoint], other_points: list[BasePoint]
    #     ):
    #         bones: dict[int, MountBone] = {}
    #         for i, bone in self.mount_bones.items():
    #             point_indices = self.bone_point_indices[i]
    #             bones[i] = self.mount_bones[i].copy(
    #                 created_points[point_indices[0]],
    #                 other_points[point_indices[1]],
    #             )
    #         return bones

    def register_repel_bone(self, points: tuple[int, int], length_factor: float) -> int:
        bone = RepelBone(self.points[points[0]], self.points[points[1]], length_factor)
        self.bone_point_indices.append(points)
        i = len(self.bone_point_indices) - 1
        self.repel_bones[i] = bone
        self.bones.append(bone.base)
        return i

    def generate_repel_bones(self, created_points: list[BasePoint]):
        bones: dict[int, RepelBone] = {}
        for i, bone in self.repel_bones.items():
            point_indices = self.bone_point_indices[i]
            bones[i] = bone.copy(
                created_points[point_indices[0]],
                created_points[point_indices[1]],
            )
        return bones

    def register_flutter_bone(self, points: tuple[int, int]) -> int:
        bone = FlutterBone(self.points[points[0]], self.points[points[1]])
        self.bone_point_indices.append(points)
        i = len(self.bone_point_indices) - 1
        self.flutter_bones[i] = bone
        self.bones.append(bone.base)
        return i

    def generate_flutter_bones(self, created_points: list[BasePoint]):
        bones: dict[int, FlutterBone] = {}
        for i, bone in self.flutter_bones.items():
            point_indices = self.bone_point_indices[i]
            bones[i] = bone.copy(
                created_points[point_indices[0]],
                created_points[point_indices[1]],
            )
        return bones

    def generate_all_bones(
        self,
        normal_bones: dict[int, NormalBone],
        repel_bones: dict[int, RepelBone],
        flutter_bones: dict[int, FlutterBone],
    ):
        bones: list[BaseBone] = []
        for bone in normal_bones:
            bones.append(bone.base)
        for bone in mount_bones:
            bones.append(bone.base)
        for bone in repel_bones:
            bones.append(bone.base)
        for bone in flutter_bones:
            bones.append(bone.base)
        return bones

    def register_joint(self, bones: tuple[int, int]):
        self.joint_bone_indices.append(bones)
        id = len(self.joint_bone_indices) - 1
        self.joints[id] = Joint(self.bones[bones[0]], self.bones[bones[1]])

    def generate_joints(self, created_bones: list[BaseBone]):
        joints: list[Joint] = []
        for i in range(len(self.joint_bone_indices)):
            bone_indices = self.joint_bone_indices[i]
            joints.append(
                self.joints[i].copy(
                    created_bones[bone_indices[0]],
                    created_bones[bone_indices[1]],
                )
            )
        return joints

    def register_mount_joint(self, bones: tuple[int, int]):
        self.joint_bone_indices.append(bones)
        id = len(self.joint_bone_indices) - 1
        self.mount_joints[id] = Joint(self.bones[bones[0]], self.bones[bones[1]])

    def generate_mount_joints(
        self, created_bones: list[BaseBone], other_bones: list[BaseBone]
    ):
        joints: list[Joint] = []
        for i in range(len(self.joint_bone_indices)):
            bone_indices = self.joint_bone_indices[i]
            joints.append(
                self.mount_joints[i].copy(
                    created_bones[bone_indices[0]],
                    other_bones[bone_indices[1]],
                )
            )
        return joints


class Skeleton:
    def __init__(
        self,
        template: SkeletonTemplate,
        intact: bool,
        contact_points: Optional[list[ContactPoint]],
        flutter_points: Optional[list[FlutterPoint]],
    ):
        self.template = template
        self.intact = intact

        if contact_points is None:
            self.contact_points = template.create_contact_points()
        else:
            self.contact_points = contact_points

        if flutter_points is None:
            self.flutter_points = template.create_flutter_points()
        else:
            self.flutter_points = flutter_points

        self.generate_skeleton()

        self.dismount_this_frame = False

    def generate_skeleton(self):
        self.all_points = self.template.generate_all_points(
            self.contact_points, self.flutter_points
        )
        self.normal_bones = self.template.generate_normal_bones(self.all_points)
        self.mount_bones = self.template.generate_mount_bones(self.all_points, None)
        self.repel_bones = self.template.generate_repel_bones(self.all_points)
        self.flutter_bones = self.template.generate_flutter_bones(self.all_points)
        self.all_bones = self.template.generate_all_bones(
            self.normal_bones, self.mount_bones, self.repel_bones, self.flutter_bones
        )
        self.joints = self.template.generate_joints(self.all_bones)
        self.mount_joints = self.template.generate_mount_joints(self.all_bones, None)

    def copy(self):
        new_contact_points: list[ContactPoint] = []
        new_flutter_points: list[FlutterPoint] = []
        for point in self.contact_points:
            new_contact_points.append(point.copy())
        for point in self.flutter_points:
            new_flutter_points.append(point.copy())
        new_skeleton = Skeleton(
            self.template,
            self.intact,
            new_contact_points,
            new_flutter_points,
        )
        return new_skeleton

    def process_initial_points(self, gravity: Vector):
        for point in self.contact_points:
            point.initial_step(gravity)

        for point in self.flutter_points:
            point.initial_step(gravity)

    def process_normal_bones(self):
        for bone in self.normal_bones:
            bone.process()

    def process_mount_bones(
        self,
        mounted,
        remounting,
    ):
        for bone in self.mount_bones:
            if mounted and not self.dismount_this_frame:
                intact = bone.get_intact(remounting)
                bone.process(remounting)

                if not intact:
                    self.dismount_this_frame = True

    def process_repel_bones(self):
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

    def process_joints(self, mounted: bool, legacy_joints: bool):
        if LRA_LEGACY_FAKIE_CHECK or legacy_joints:
            # Don't process joints if dismounted
            if not mounted or self.dismount_this_frame:
                return

        for joint in self.joints:
            if self.intact and joint.should_break():
                self.intact = False

    def process_mount_joints(self, mounted: bool):
        if LRA_LEGACY_FAKIE_CHECK:
            # Don't process mount joints if dismounted
            if not mounted or self.dismount_this_frame:
                return

        for joint in self.mount_joints:
            if mounted and not self.dismount_this_frame and joint.should_break():
                self.dismount_this_frame = True

    def process(
        self,
        other: Optional["Skeleton"],
        gravity: Vector,
        grid: Grid,
        mounted: bool,
        remounting: bool,
        legacy_joints: bool,
    ):
        self.dismount_this_frame = False

        # momentum
        self.process_initial_points(gravity)
        if other != None:
            other.process_initial_points(gravity)

        for _ in range(6):
            # bones
            self.process_normal_bones()
            self.process_mount_bones(mounted, remounting)
            self.process_repel_bones()
            if other != None:
                other.process_normal_bones()
                other.process_mount_bones(mounted, remounting)
                other.process_repel_bones()

            # line collisions
            self.process_collisions(grid)
            if other != None:
                other.process_collisions(grid)

        # flutter bones (like scarf)
        self.process_flutter_bones()
        if other != None:
            other.process_flutter_bones()

        # dismount skeletons
        self.process_mount_joints(mounted)
        if other != None:
            other.process_mount_joints(mounted)

        # break skeletons
        self.process_joints(mounted, legacy_joints)
        if other != None:
            other.process_joints(mounted, legacy_joints)

        return self.dismount_this_frame
