from engine.grid import Grid
from engine.vector import Vector
from engine.point import BasePoint, ContactPoint, FlutterPoint
from engine.bone import BaseBone, NormalBone, RepelBone, FlutterBone, FragileBone
from engine.binding import Binding, BindingTrigger
from engine.constants import USE_COM_SCARF

from typing import TypedDict, Union
import math

# TODO .com remounting v1, v2, lra remount


class InitialEntityParams(TypedDict):
    POSITION: Vector
    VELOCITY: Vector
    ROTATION: float  # In degrees
    REMOUNT: bool


class Entity:
    def __init__(self):
        # List of colliding physics points (contact points)
        self.structural_points: list[ContactPoint] = []
        # List of non-colliding physics points (scarf, etc.)
        self.flutter_points: list[FlutterPoint] = []
        # Connect structural points
        self.structural_bones: list[Union[NormalBone, RepelBone, FragileBone]] = []
        # Connect flutter points
        self.flutter_bones: list[FlutterBone] = []
        self.binding_triggers: list[BindingTrigger] = []
        # Whether this entity is attached to another entity
        self.mounted = True
        # Whether this entity is able to rejoin with another entity (regardless of mounted state)
        # This is shared between the sled broken state and whether the rider can remount initially
        self.can_remount = False
        # TODO remount state booleans/ints here

    def set_can_remount(self, can_remount: bool):
        self.can_remount = can_remount

    def set_mounted(self, mounted: bool):
        self.mounted = mounted

    # This updates the contact points with initial position, velocity, and a rotation
    # about the tail, as well as setting the remount property
    def apply_initial_state(
        self, init_state: InitialEntityParams, rotation_origin: Vector
    ):
        self.can_remount = init_state["REMOUNT"]

        origin = rotation_origin
        # Note that the use of cos and sin here is not exactly the same as javascript
        # engines might implement it
        # This gets tested with 50 degrees so it happens to pass the test case,
        # but this may not give the same output for every input
        cos_theta = math.cos(init_state["ROTATION"] * math.pi / 180)
        sin_theta = math.sin(init_state["ROTATION"] * math.pi / 180)
        all_points = self.structural_points + self.flutter_points

        for point in all_points:
            offset = point.base.position - origin
            point.base.update_state(
                Vector(
                    origin.x + offset.x * cos_theta - offset.y * sin_theta,
                    origin.y + offset.x * sin_theta + offset.y * cos_theta,
                ),
                point.base.velocity,
                point.base.previous_position,
            )

        for point in all_points:
            start_position = point.base.position + init_state["POSITION"]
            start_velocity = point.base.velocity + init_state["VELOCITY"]
            point.base.update_state(
                start_position, start_velocity, start_position - start_velocity
            )

    def add_contact_point(self, position: Vector, friction: float) -> ContactPoint:
        base_point = BasePoint(position, Vector(0, 0), position)
        point = ContactPoint(base_point, friction)
        self.structural_points.append(point)
        return point

    def add_flutter_point(self, position: Vector, air_friction: float) -> FlutterPoint:
        base_point = BasePoint(position, Vector(0, 0), position)
        point = FlutterPoint(base_point, air_friction)
        self.flutter_points.append(point)
        return point

    def add_bind_trigger(
        self,
        binding: Binding,
        joint1: tuple[ContactPoint, ContactPoint],
        joint2: tuple[ContactPoint, ContactPoint],
    ) -> BindingTrigger:
        bind_trigger = BindingTrigger(binding, joint1, joint2)
        self.binding_triggers.append(bind_trigger)
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
        # TODO
        return Entity()

    def process_initial_step(self, gravity: Vector):
        for point in self.structural_points:
            point.initial_step(gravity)

        for point in self.flutter_points:
            point.initial_step(gravity)

    def process_structural_bones(self):
        for bone in self.structural_bones:
            bone.process()

    def process_collisions(self, grid: Grid):
        for point in self.structural_points:
            interacting_lines = grid.get_interacting_lines(point)
            for line in interacting_lines:
                new_pos, new_prev_pos = line.interact(point)
                point.base.update_state(new_pos, point.base.velocity, new_prev_pos)

    def process_bind_triggers(self):
        for bind in self.binding_triggers:
            bind.process()

    def process_flutter_bones(self):
        for bone in self.flutter_bones:
            bone.process()

    def get_all_points(self) -> list[BasePoint]:
        all_points = []

        for structural_point in self.structural_points:
            all_points.append(structural_point.base)

        for flutter_point in self.flutter_points:
            all_points.append(flutter_point.base)

        return all_points

    def get_average_position(self) -> Vector:
        all_points = self.get_all_points()
        total_x = 0
        total_y = 0
        num_points = len(all_points)

        if num_points == 0:
            return Vector(0, 0)

        for point in all_points:
            total_x += point.position.x
            total_y += point.position.y

        return Vector(total_x / num_points, total_y / num_points)


def create_default_rider(init_state: InitialEntityParams) -> Entity:
    entity = Entity()
    FRAGILE_BONE_ENDURANCE = 0.057
    REPEL_BONE_LENGTH_FACTOR = 0.5

    if USE_COM_SCARF:
        SCARF_FRICTION = 0.2
    else:
        SCARF_FRICTION = 0.1

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
    SCARF_0 = entity.add_flutter_point(Vector(3, -5.5), SCARF_FRICTION)
    SCARF_1 = entity.add_flutter_point(Vector(1, -5.5), SCARF_FRICTION)
    SCARF_2 = entity.add_flutter_point(Vector(-1, -5.5), SCARF_FRICTION)
    SCARF_3 = entity.add_flutter_point(Vector(-3, -5.5), SCARF_FRICTION)
    SCARF_4 = entity.add_flutter_point(Vector(-5, -5.5), SCARF_FRICTION)
    SCARF_5 = entity.add_flutter_point(Vector(-7, -5.5), SCARF_FRICTION)
    SCARF_6 = entity.add_flutter_point(Vector(-9, -5.5), SCARF_FRICTION)

    # Create bindings that get triggered by joint crossings
    MOUNTED_BINDING = Binding(
        lambda: entity.mounted,
        lambda x: entity.set_mounted(x),
    )
    SLED_BROKEN_BINDING = Binding(
        lambda: entity.can_remount,
        lambda x: entity.set_can_remount(x),
    )

    # Add the bindings with their joints
    entity.add_bind_trigger(MOUNTED_BINDING, (SHOULDER, BUTT), (STRING, PEG))
    entity.add_bind_trigger(MOUNTED_BINDING, (PEG, TAIL), (STRING, PEG))
    entity.add_bind_trigger(SLED_BROKEN_BINDING, (PEG, TAIL), (STRING, PEG))

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
    # (because it does not affect bone length)
    entity.apply_initial_state(init_state, TAIL.base.position)

    return entity
