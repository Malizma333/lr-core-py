from engine.vector import Vector


# Contact point of an entity, separated into this file to avoid circular imports
class ContactPoint:
    def __init__(self, position: Vector, velocity: Vector, friction: float):
        self.friction = friction
        self.position = position.copy()
        self.velocity = velocity.copy()
        self.pending_resistance = Vector(0, 0)
        self.previous_position = position - velocity

    def update_state(self, new_pos: Vector, new_vel: Vector, new_prev_pos: Vector):
        self.position = new_pos.copy()
        self.velocity = new_vel.copy()
        self.previous_position = new_prev_pos.copy()
        self.pending_resistance = self.previous_position - self.position
        # print("update", self.position - self.velocity == self.previous_position)

    def __repr__(self):
        return f"ContactPoint(position: {self.position}, velocity: {self.velocity}, prev_position: {self.previous_position})"
