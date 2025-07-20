# TODO remount physics? + remount versions (lra vs .com)?
# TODO scarf physics? + scarf versions (lra vs .com)?

from engine.grid import Grid
from engine.vector import Vector
from engine.contact_point import ContactPoint

from enum import Enum
from typing import TypedDict, Union
import math

FRAGILE_BONE_ENDURANCE = 0.057
REPEL_BONE_LENGTH_FACTOR = 0.5


# Joints that cause breakages if they cross other joints
class BindJoint:
    def __init__(self, point1: ContactPoint, point2: ContactPoint):
        self.point1 = point1
        self.point2 = point2

    def get_vector(self) -> Vector:
        return self.point2.position - self.point1.position


# Bindings used to mark bones that get broken by joints crossing
class Binding:
    def __init__(self):
        self.broken = False


# Structure containing a binding and the bind joints that trigger it
class BindTrigger:
    def __init__(self, binding: Binding, bind_joints: tuple[BindJoint, BindJoint]):
        self.binding = binding
        self.bind_joints = bind_joints

    def process(self):
        delta1 = self.bind_joints[0].get_vector()
        delta2 = self.bind_joints[1].get_vector()
        if delta1.cross(delta2) < 0:
            self.binding.broken = True


class BaseBone:
    def __init__(self, point1: ContactPoint, point2: ContactPoint):
        self.point1 = point1
        self.point2 = point2
        self.rest_length = point1.position.distance_from(point2.position)


# Bones connecting points to keep them as the same structure
class NormalBone:
    def __init__(self, base: BaseBone):
        self.base = base

    def process(self):
        position1 = self.base.point1.position
        position2 = self.base.point2.position
        bone_vector = position1 - position2
        current_length = bone_vector.length()
        rest_length = self.base.rest_length

        if current_length == 0:
            adjustment = 0
        else:
            adjustment = (current_length - rest_length) / current_length * 0.5

        bone_vector *= adjustment

        self.base.point1.set_position(position1 - bone_vector)
        self.base.point2.set_position(position2 + bone_vector)


# Bones that can also break after a certain threshold
class FragileBone:
    def __init__(self, base: BaseBone, endurance: float, binding: Binding):
        self.base = base
        self.endurance = endurance
        self.binding = binding

    def process(self):
        position1 = self.base.point1.position
        position2 = self.base.point2.position
        bone_vector = position1 - position2
        current_length = bone_vector.length()
        rest_length = self.base.rest_length

        if current_length == 0:
            adjustment = 0
        else:
            adjustment = (current_length - rest_length) / current_length * 0.5

        if self.binding.broken or adjustment > self.endurance * rest_length * 0.5:
            self.binding.broken = True
            return

        bone_vector *= adjustment

        self.base.point1.set_position(position1 - bone_vector)
        self.base.point2.set_position(position2 + bone_vector)


# Bones designed to "repel" points without connecting them with a traditional bone
class RepelBone:
    def __init__(self, base: BaseBone, length_factor: float):
        self.base = base
        self.length_factor = length_factor

    def process(self):
        position1 = self.base.point1.position
        position2 = self.base.point2.position
        bone_vector = position1 - position2
        current_length = bone_vector.length()
        rest_length = self.base.rest_length * self.length_factor

        if current_length >= rest_length:
            return

        if current_length == 0:
            adjustment = 0
        else:
            adjustment = (current_length - rest_length) / current_length * 0.5

        bone_vector *= adjustment

        self.base.point1.set_position(position1 - bone_vector)
        self.base.point2.set_position(position2 + bone_vector)


class EntityState(Enum):
    MOUNTED = 0
    DISMOUNTED = 1


class InitialEntityParams(TypedDict):
    POSITION: Vector
    VELOCITY: Vector
    ROTATION: float
    REMOUNT: bool


class Entity:
    def __init__(self):
        self.bones: list[Union[NormalBone, RepelBone, FragileBone]] = []
        self.points: list[ContactPoint] = []
        self.bind_triggers: list[BindTrigger] = []
        self.state: EntityState = EntityState.MOUNTED
        # TODO Boolean for remount enabled, which sets the sled and bosh remount enabled, unless the sled breaks
        # TODO Boolean for remountable state, which is what gets set by remount enabled

    def apply_initial_state(
        self, init_state: InitialEntityParams, rotation_origin: Vector
    ):
        # TODO: Remount

        origin = rotation_origin
        cos_theta = math.cos(init_state["ROTATION"])
        sin_theta = math.sin(init_state["ROTATION"])

        for i, point in enumerate(self.points):
            offset = point.position - origin
            self.points[i].set_position(
                Vector(
                    origin.x + offset.x * cos_theta - offset.y * sin_theta,
                    origin.y + offset.x * sin_theta + offset.y * cos_theta,
                )
            )

        for i, point in enumerate(self.points):
            self.points[i].set_position(point.position + init_state["POSITION"])
            self.points[i].set_velocity(point.velocity + init_state["VELOCITY"])
            self.points[i].set_prev_position(
                self.points[i].position - self.points[i].velocity
            )

    def add_point(self, position: Vector, friction: float) -> ContactPoint:
        point = ContactPoint(position, Vector(0, 0), friction)
        self.points.append(point)
        return point

    def add_normal_bone(self, point1: ContactPoint, point2: ContactPoint):
        self.bones.append(NormalBone(BaseBone(point1, point2)))

    def add_fragile_bone(
        self,
        point1: ContactPoint,
        point2: ContactPoint,
        endurance: float,
        binding: Binding,
    ):
        self.bones.append(FragileBone(BaseBone(point1, point2), endurance, binding))

    def add_repel_bone(
        self, point1: ContactPoint, point2: ContactPoint, length_factor: float
    ):
        self.bones.append(RepelBone(BaseBone(point1, point2), length_factor))

    def add_bind_trigger(self, binding: Binding, joint1: BindJoint, joint2: BindJoint):
        self.bind_triggers.append(BindTrigger(binding, bind_joints=(joint1, joint2)))

    def deep_copy(self):
        new_entity = Entity()
        new_entity.state = self.state
        # TODO see if we can get rid of these in favor of indices
        point_map: dict[ContactPoint, ContactPoint] = {}
        bind_map: dict[Binding, Binding] = {}

        # Copy each contact point and add points to map
        for point in self.points:
            new_point = new_entity.add_point(point.position, point.friction)
            new_point.set_velocity(point.velocity.copy())
            new_point.set_prev_position(point.previous_position.copy())
            point_map[point] = new_point

        # Copy each bind trigger structure and add bindings to map
        for bind_trigger in self.bind_triggers:
            point1 = point_map[bind_trigger.bind_joints[0].point1]
            point2 = point_map[bind_trigger.bind_joints[0].point2]
            point3 = point_map[bind_trigger.bind_joints[1].point1]
            point4 = point_map[bind_trigger.bind_joints[1].point2]
            bind_joint1 = BindJoint(point1, point2)
            bind_joint2 = BindJoint(point3, point4)
            new_binding = Binding()
            new_binding.broken = bind_trigger.binding.broken
            bind_map[bind_trigger.binding] = new_binding
            new_entity.add_bind_trigger(new_binding, bind_joint1, bind_joint2)

        # Copy each bone and use point map to reconstruct bone endpoints
        for bone in self.bones:
            new_bone_p1 = point_map[bone.base.point1]
            new_bone_p2 = point_map[bone.base.point2]
            if type(bone) == NormalBone:
                new_entity.add_normal_bone(new_bone_p1, new_bone_p2)
            elif type(bone) == FragileBone:
                binding = bind_map[bone.binding]
                new_entity.add_fragile_bone(
                    new_bone_p1, new_bone_p2, bone.endurance, binding
                )
            elif type(bone) == RepelBone:
                new_entity.add_repel_bone(new_bone_p1, new_bone_p2, bone.length_factor)
            # Copy original rest length
            new_entity.bones[-1].base.rest_length = bone.base.rest_length

        return new_entity

    def initial_step(self, gravity: Vector):
        for point_index, point in enumerate(self.points):
            new_velocity = point.position - point.previous_position + gravity
            current_position = point.position.copy()
            self.points[point_index].set_velocity(new_velocity)
            self.points[point_index].set_prev_position(current_position)
            self.points[point_index].set_position(current_position + new_velocity)

    def process_bones(self):
        for bone in self.bones:
            bone.process()

    def process_collisions(self, grid: Grid):
        for point_index, point in enumerate(self.points):
            interacting_lines = grid.get_interacting_lines(point)
            for line in interacting_lines:
                new_pos, new_prev_pos = line.interact(point)
                point.set_position(new_pos)
                point.set_prev_position(new_prev_pos)

    def process_bind_triggers(self):
        for bind in self.bind_triggers:
            bind.process()


def create_default_rider(init_state: InitialEntityParams) -> Entity:
    entity = Entity()

    # Create the contact points first, at their initial positions
    # Order doesn't really matter, added in this order for ease of conversion
    # to linerider.com order in test cases
    PEG = entity.add_point(Vector(0.0, 0.0), 0.8)
    TAIL = entity.add_point(Vector(0.0, 5.0), 0.0)
    NOSE = entity.add_point(Vector(15.0, 5.0), 0.0)
    STRING = entity.add_point(Vector(17.5, 0.0), 0.0)
    BUTT = entity.add_point(Vector(5.0, 0.0), 0.8)
    SHOULDER = entity.add_point(Vector(5.0, -5.5), 0.8)
    LEFT_HAND = entity.add_point(Vector(11.5, -5.0), 0.1)
    RIGHT_HAND = entity.add_point(Vector(11.5, -5.0), 0.1)
    LEFT_FOOT = entity.add_point(Vector(10.0, 5.0), 0.0)
    RIGHT_FOOT = entity.add_point(Vector(10.0, 5.0), 0.0)

    # Create joints that can cause breakages
    SHOULDER_BUTT_JOINT = BindJoint(SHOULDER, BUTT)
    STRING_PEG_JOINT = BindJoint(STRING, PEG)
    PEG_TAIL_JOINT = BindJoint(PEG, TAIL)

    # Create bindings that get triggered by joint crossings
    MOUNTED_BINDING = Binding()
    SLED_BROKEN_BINDING = Binding()  # TODO: Should this be generalized for entities?

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

    # Apply initial state once everything is initialized
    entity.apply_initial_state(init_state, TAIL.position)

    return entity
