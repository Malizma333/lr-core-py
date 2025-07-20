from engine.vector import Vector


# Contact point of an entity, separated into this file to avoid circular imports
class ContactPoint:
    def __init__(
        self,
        position: Vector,
        velocity: Vector,
        previous_position: Vector,
        friction: float,
    ):
        self.friction = friction
        self.position = position.copy()
        self.velocity = velocity.copy()
        # Previous position is not necessarily (position - velocity), as it's
        # used to track effects of friction and acceleration, and can't be
        # refactored due to floating point stuff :(
        self.previous_position = previous_position.copy()

    # A very specific state update function for updating fields of the contact point
    def update_state(self, new_pos: Vector, new_vel: Vector, new_prev_pos: Vector):
        self.position = new_pos.copy()
        self.velocity = new_vel.copy()
        self.previous_position = new_prev_pos.copy()

    def __repr__(self):
        return f"ContactPoint(position: {self.position}, velocity: {self.velocity}, prev_position: {self.previous_position})"
