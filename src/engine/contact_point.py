from engine.vector import Vector


class ContactPoint:
    def __init__(self, position: Vector, velocity: Vector, friction: float):
        self.friction = friction
        self.position = position.copy()
        self.velocity = velocity.copy()
        self.previous_position = position - velocity

    def set_position(self, new_position: Vector):
        self.position = new_position.copy()

    def set_velocity(self, new_velocity: Vector):
        self.velocity = new_velocity.copy()

    def set_prev_position(self, new_prev_position: Vector):
        self.previous_position = new_prev_position.copy()

    def __repr__(self):
        return f"ContactPoint(position: {self.position}, velocity: {self.velocity}, prev_position: {self.previous_position})"
