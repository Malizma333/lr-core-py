# Math utilities

from typing import Union, Self


class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    # v1 + v2
    def __add__(self, other: Self):
        return Vector(self.x + other.x, self.y + other.y)

    # v1 - v2
    def __sub__(self, other: Self):
        return Vector(self.x - other.x, self.y - other.y)

    # v1 * scalar
    def __mul__(self, scalar: Union[float, int]):
        return Vector(self.x * scalar, self.y * scalar)

    # v1 / scalar
    def __truediv__(self, scalar: Union[float, int]):
        return Vector(self.x / scalar, self.y / scalar)

    # v1 == v2
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    # v1 @ v2 = dot product
    def __matmul__(self, other: Self):
        return self.x * other.x + self.y * other.y

    # scalar * v1
    def __rmul__(self, scalar: Union[float, int]):
        return self * scalar

    # str(v1), etc
    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

    def magnitude(self) -> float:
        return (self.x * self.x + self.y * self.y) ** 0.5

    def unit(self):
        return Vector(self.x / self.magnitude(), self.y / self.magnitude())

    def copy(self):
        return Vector(self.x, self.y)

    def rot_ccw(self):
        return Vector(-self.y, self.x)

    def rot_cw(self):
        return Vector(self.y, -self.x)

    def distance_from(self, other: Self):
        delta = self - other
        return delta.magnitude()
