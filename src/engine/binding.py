from engine.point import ContactPoint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Avoid circular importing of types
    from engine.entity import Entity, EntityState


# Bindings used to provide accessors to entity state
class Binding:
    def __init__(self, entity: "Entity", attribute: "EntityState"):
        self.entity = entity
        self.attribute = attribute

    def get(self):
        return self.entity.binded_states[self.attribute.name]

    def set(self, value: bool):
        self.entity.binded_states[self.attribute.name] = value


# Structure containing a binding and the bind joints that trigger it to break
class BindingTrigger:
    def __init__(
        self,
        binding: Binding,
        bind_joint1: tuple[ContactPoint, ContactPoint],
        bind_joint2: tuple[ContactPoint, ContactPoint],
    ):
        self.binding = binding
        self.bind_joints = (bind_joint1, bind_joint2)

    def process(self):
        delta1 = (
            self.bind_joints[0][1].base.position - self.bind_joints[0][0].base.position
        )
        delta2 = (
            self.bind_joints[1][1].base.position - self.bind_joints[1][0].base.position
        )
        if delta1.cross(delta2) < 0:
            self.binding.set(False)
