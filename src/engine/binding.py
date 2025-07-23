from engine.vector import Vector
from engine.point import ContactPoint, FlutterPoint

from typing import Union


# Joints that cause breakages if they cross other joints
class BindJoint:
    def __init__(
        self,
        point1: Union[ContactPoint, FlutterPoint],
        point2: Union[ContactPoint, FlutterPoint],
    ):
        self.point1 = point1
        self.point2 = point2

    def get_vector(self) -> Vector:
        return self.point2.base.position - self.point1.base.position


# TODO refactor bindings into internal entity dictionary with [str, bool] state
# Bindings used to mark bones that get broken by joints crossing
class Binding:
    def __init__(self, index: int):
        # Index within entity list of bindings
        self.index = index
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
