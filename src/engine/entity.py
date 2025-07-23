from engine.grid import Grid
from engine.vector import Vector
from engine.point import BasePoint, ContactPoint, FlutterPoint
from engine.bone import BaseBone, NormalBone, RepelBone, FlutterBone, FragileBone
from engine.binding import Binding, BindJoint, BindTrigger

from typing import TypedDict, Union
import math

FRAGILE_BONE_ENDURANCE = 0.057
REPEL_BONE_LENGTH_FACTOR = 0.5
# TODO .com remounting v1 vs v2?


class InitialEntityParams(TypedDict):
    POSITION: Vector
    VELOCITY: Vector
    ROTATION: float
    REMOUNT: bool


class Entity:
    def __init__(self):
        self.structural_bones: list[Union[NormalBone, RepelBone, FragileBone]] = []
        self.flutter_bones: list[FlutterBone] = []
        self.points: list[Union[ContactPoint, FlutterPoint]] = []
        self.bind_triggers: list[BindTrigger] = []
        # TODO
        #  Boolean for remount enabled, which sets for both sled and rider entities whether they can join other entities
        #  Gets set to false if sled breaks
        #  Boolean for remountable state, which is what gets set by remount enabled

    # This updates the contact points with initial position, velocity, and a rotation
    # about the tail, as well as setting the remount property
    def apply_initial_state(
        self, init_state: InitialEntityParams, rotation_origin: Vector
    ):
        # TODO: Set remount boolean

        origin = rotation_origin
        cos_theta = math.cos(init_state["ROTATION"])
        sin_theta = math.sin(init_state["ROTATION"])

        for i, point in enumerate(self.points):
            offset = point.base.position - origin
            self.points[i].base.update_state(
                Vector(
                    origin.x + offset.x * cos_theta - offset.y * sin_theta,
                    origin.y + offset.x * sin_theta + offset.y * cos_theta,
                ),
                self.points[i].base.velocity,
                self.points[i].base.previous_position,
            )

        for i, point in enumerate(self.points):
            start_position = point.base.position + init_state["POSITION"]
            start_velocity = point.base.velocity + init_state["VELOCITY"]
            self.points[i].base.update_state(
                start_position, start_velocity, start_position - start_velocity
            )

    def add_contact_point(self, position: Vector, friction: float) -> ContactPoint:
        next_index = len(self.points)
        base_point = BasePoint(position, Vector(0, 0), position, next_index)
        point = ContactPoint(base_point, friction)
        self.points.append(point)
        return point

    def add_flutter_point(self, position: Vector, air_friction: float) -> FlutterPoint:
        next_index = len(self.points)
        base_point = BasePoint(position, Vector(0, 0), position, next_index)
        point = FlutterPoint(base_point, air_friction)
        self.points.append(point)
        return point

    def add_bind_trigger(
        self, binding: Binding, joint1: BindJoint, joint2: BindJoint
    ) -> BindTrigger:
        bind_trigger = BindTrigger(binding, bind_joints=(joint1, joint2))
        self.bind_triggers.append(bind_trigger)
        return bind_trigger

    def add_normal_bone(
        self,
        point1: Union[ContactPoint, FlutterPoint],
        point2: Union[ContactPoint, FlutterPoint],
    ) -> NormalBone:
        bone = NormalBone(BaseBone(point1, point2))
        self.structural_bones.append(bone)
        return bone

    def add_fragile_bone(
        self,
        point1: Union[ContactPoint, FlutterPoint],
        point2: Union[ContactPoint, FlutterPoint],
        endurance: float,
        binding: Binding,
    ) -> FragileBone:
        bone = FragileBone(BaseBone(point1, point2), endurance, binding)
        self.structural_bones.append(bone)
        return bone

    def add_repel_bone(
        self,
        point1: Union[ContactPoint, FlutterPoint],
        point2: Union[ContactPoint, FlutterPoint],
        length_factor: float,
    ) -> RepelBone:
        bone = RepelBone(BaseBone(point1, point2), length_factor)
        self.structural_bones.append(bone)
        return bone

    def add_flutter_bone(
        self,
        point1: Union[ContactPoint, FlutterPoint],
        point2: Union[ContactPoint, FlutterPoint],
    ) -> FlutterBone:
        bone = FlutterBone(BaseBone(point1, point2))
        self.flutter_bones.append(bone)
        return bone

    def deep_copy(self):
        new_entity = Entity()
        # Point and binding maps used to reconstruct point and binding references
        point_map: dict[int, Union[ContactPoint, FlutterPoint]] = {}
        binding_map: dict[int, Binding] = {}

        # Copy each contact point and add points to map
        for point in self.points:
            if isinstance(point, ContactPoint):
                new_point = new_entity.add_contact_point(
                    point.base.position, point.friction
                )
            else:
                new_point = new_entity.add_flutter_point(
                    point.base.position, point.air_friction
                )

            new_point.base.update_state(
                new_point.base.position,
                point.base.velocity,
                point.base.previous_position,
            )
            point_map[point.base.index] = new_point

        # Copy each bind trigger structure and add bindings to map
        for bind_trigger in self.bind_triggers:
            point1 = point_map[bind_trigger.bind_joints[0].point1.base.index]
            point2 = point_map[bind_trigger.bind_joints[0].point2.base.index]
            point3 = point_map[bind_trigger.bind_joints[1].point1.base.index]
            point4 = point_map[bind_trigger.bind_joints[1].point2.base.index]
            bind_joint1 = BindJoint(point1, point2)
            bind_joint2 = BindJoint(point3, point4)
            new_binding = Binding(bind_trigger.binding.index)
            new_binding.broken = bind_trigger.binding.broken
            binding_map[bind_trigger.binding.index] = new_binding
            new_entity.add_bind_trigger(new_binding, bind_joint1, bind_joint2)

        # Copy structural bones
        for bone in self.structural_bones:
            new_bone_p1 = point_map[bone.base.point1.base.index]
            new_bone_p2 = point_map[bone.base.point2.base.index]
            if isinstance(bone, NormalBone):
                new_bone = new_entity.add_normal_bone(new_bone_p1, new_bone_p2)
            elif isinstance(bone, FragileBone):
                new_bone = new_entity.add_fragile_bone(
                    new_bone_p1,
                    new_bone_p2,
                    bone.endurance,
                    binding_map[bone.binding.index],
                )
            else:
                new_bone = new_entity.add_repel_bone(new_bone_p1, new_bone_p2, 1)
            new_bone.base.rest_length = bone.base.rest_length

        # Copy flutter bones
        for bone in self.flutter_bones:
            new_bone_p1 = point_map[bone.base.point1.base.index]
            new_bone_p2 = point_map[bone.base.point2.base.index]
            new_flutter_bone = new_entity.add_flutter_bone(new_bone_p1, new_bone_p2)
            new_flutter_bone.base.rest_length = bone.base.rest_length

        return new_entity

    def initial_step(self, gravity: Vector):
        for point in self.points:
            point.initial_step(gravity)

    def process_structural_bones(self):
        for bone in self.structural_bones:
            bone.process()

    def process_collisions(self, grid: Grid):
        for point_index, point in enumerate(self.points):
            if isinstance(point, ContactPoint):
                interacting_lines = grid.get_interacting_lines(point)
                for line in interacting_lines:
                    new_pos, new_prev_pos = line.interact(point)
                    point.base.update_state(new_pos, point.base.velocity, new_prev_pos)

    def process_bind_triggers(self):
        for bind in self.bind_triggers:
            bind.process()

    def process_flutter_bones(self):
        for bone in self.flutter_bones:
            bone.process()


def create_default_rider(init_state: InitialEntityParams) -> Entity:
    entity = Entity()

    # Create the contact points first, at their initial positions
    # Order doesn't really matter, added in this order to match linerider.com
    # based test cases
    PEG = entity.add_contact_point(Vector(0.0, 0.0), 0.8)
    TAIL = entity.add_contact_point(Vector(0.0, 5.0), 0.0)
    NOSE = entity.add_contact_point(Vector(15.0, 5.0), 0.0)
    STRING = entity.add_contact_point(Vector(17.5, 0.0), 0.0)
    BUTT = entity.add_contact_point(Vector(5.0, 0.0), 0.8)
    SHOULDER = entity.add_contact_point(Vector(5.0, -5.5), 0.8)
    RIGHT_HAND = entity.add_contact_point(Vector(11.5, -5.0), 0.1)
    LEFT_HAND = entity.add_contact_point(Vector(11.5, -5.0), 0.1)
    LEFT_FOOT = entity.add_contact_point(Vector(10.0, 5.0), 0.0)
    RIGHT_FOOT = entity.add_contact_point(Vector(10.0, 5.0), 0.0)
    SCARF_0 = entity.add_flutter_point(Vector(3, -5.5), 0.2)
    SCARF_1 = entity.add_flutter_point(Vector(1, -5.5), 0.2)
    SCARF_2 = entity.add_flutter_point(Vector(-1, -5.5), 0.2)
    SCARF_3 = entity.add_flutter_point(Vector(-3, -5.5), 0.2)
    SCARF_4 = entity.add_flutter_point(Vector(-5, -5.5), 0.2)
    SCARF_5 = entity.add_flutter_point(Vector(-7, -5.5), 0.2)
    SCARF_6 = entity.add_flutter_point(Vector(-9, -5.5), 0.2)

    # Create joints that can cause breakages
    SHOULDER_BUTT_JOINT = BindJoint(SHOULDER, BUTT)
    STRING_PEG_JOINT = BindJoint(STRING, PEG)
    PEG_TAIL_JOINT = BindJoint(PEG, TAIL)

    # Create bindings that get triggered by joint crossings
    MOUNTED_BINDING = Binding(0)
    SLED_BROKEN_BINDING = Binding(1)  # TODO: Should this be generalized for entities?

    # Add the bindings with their joints
    entity.add_bind_trigger(MOUNTED_BINDING, SHOULDER_BUTT_JOINT, STRING_PEG_JOINT)
    entity.add_bind_trigger(MOUNTED_BINDING, PEG_TAIL_JOINT, STRING_PEG_JOINT)
    entity.add_bind_trigger(SLED_BROKEN_BINDING, PEG_TAIL_JOINT, STRING_PEG_JOINT)

    # Create bones now that joints and bindings are initialized
    entity.add_normal_bone(PEG, TAIL)
    entity.add_normal_bone(TAIL, NOSE)
    entity.add_normal_bone(NOSE, STRING)
    entity.add_normal_bone(STRING, PEG)
    entity.add_normal_bone(PEG, NOSE)
    entity.add_normal_bone(STRING, TAIL)
    entity.add_fragile_bone(PEG, BUTT, FRAGILE_BONE_ENDURANCE, MOUNTED_BINDING)
    entity.add_fragile_bone(TAIL, BUTT, FRAGILE_BONE_ENDURANCE, MOUNTED_BINDING)
    entity.add_fragile_bone(NOSE, BUTT, FRAGILE_BONE_ENDURANCE, MOUNTED_BINDING)
    entity.add_normal_bone(SHOULDER, BUTT)
    entity.add_normal_bone(SHOULDER, LEFT_HAND)
    entity.add_normal_bone(SHOULDER, RIGHT_HAND)
    entity.add_normal_bone(BUTT, LEFT_FOOT)
    entity.add_normal_bone(BUTT, RIGHT_FOOT)
    entity.add_normal_bone(SHOULDER, RIGHT_HAND)
    entity.add_fragile_bone(SHOULDER, PEG, FRAGILE_BONE_ENDURANCE, MOUNTED_BINDING)
    entity.add_fragile_bone(STRING, LEFT_HAND, FRAGILE_BONE_ENDURANCE, MOUNTED_BINDING)
    entity.add_fragile_bone(STRING, RIGHT_HAND, FRAGILE_BONE_ENDURANCE, MOUNTED_BINDING)
    entity.add_fragile_bone(LEFT_FOOT, NOSE, FRAGILE_BONE_ENDURANCE, MOUNTED_BINDING)
    entity.add_fragile_bone(RIGHT_FOOT, NOSE, FRAGILE_BONE_ENDURANCE, MOUNTED_BINDING)
    entity.add_repel_bone(SHOULDER, LEFT_FOOT, REPEL_BONE_LENGTH_FACTOR)
    entity.add_repel_bone(SHOULDER, RIGHT_FOOT, REPEL_BONE_LENGTH_FACTOR)
    entity.add_flutter_bone(SHOULDER, SCARF_0)
    entity.add_flutter_bone(SCARF_0, SCARF_1)
    entity.add_flutter_bone(SCARF_1, SCARF_2)
    entity.add_flutter_bone(SCARF_2, SCARF_3)
    entity.add_flutter_bone(SCARF_3, SCARF_4)
    entity.add_flutter_bone(SCARF_4, SCARF_5)
    entity.add_flutter_bone(SCARF_5, SCARF_6)

    # Apply initial state once everything is initialized
    # Note that this must be applied after bone constraints are calculated
    entity.apply_initial_state(init_state, TAIL.base.position)

    return entity
