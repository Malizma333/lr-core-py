from engine.bone import BaseBone
from enum import Enum


class JointType(Enum):
    INNER = 0
    MOUNT = 1


# Joint between two bones that can break
class Joint:
    def __init__(
        self,
        bone1: BaseBone,
        bone2: BaseBone,
    ):
        self.bone1 = bone1
        self.bone2 = bone2

    def should_break(self):
        delta1 = self.bone1.get_vector()
        delta2 = self.bone2.get_vector()
        return delta1.cross(delta2) < 0
