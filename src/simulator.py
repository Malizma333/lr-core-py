import tkinter as tk
import json

from engine.engine import Engine, FRAMES_PER_SECOND
from engine.vector import Vector
from engine.entity import Entity, EntityState, NormalBone, FragileBone, RepelBone
from engine.line import PhysicsLine, LINE_HITBOX_HEIGHT
from utils.convert import convert_lines, convert_entities, convert_version


class TrackSimulator:
    ZOOM = 12
    CP_RADIUS = 2
    BONE_WIDTH = 0.25
    MV_LENGTH = 3
    MV_WIDTH = 0.25
    MV_COLOR = "green"
    CP_COLOR = "white"
    EXTENSION_DRAW_WIDTH = 1
    LINE_DRAW_WIDTH = 2

    def __init__(self, track_path: str):
        self.track_path = track_path
        self.track = json.load(open(track_path, "r"))
        version = convert_version(self.track["version"])
        self.entities = convert_entities(self.track["riders"])
        self.lines = convert_lines(self.track["lines"])
        self.engine = Engine(version, self.entities, self.lines)

        self.root = tk.Tk()
        self.root.title("Line Rider Python Engine")
        self.canvas = tk.Canvas(self.root, width=1280, height=720, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas_cache = []
        self.canvas_center = Vector(
            int(self.canvas["width"]) / 2, int(self.canvas["height"]) / 2
        )
        self.origin = Vector(0, 0)

        self.frame = 0
        self.focused_entity = 0
        self.playing = False
        self.current_draw_index = 0

        self._bind_keys()
        self.root.bind("<Configure>", self._on_resize)
        self._update()
        self._tick()
        self.canvas.focus_set()
        self.root.mainloop()

    def _bind_keys(self):
        self.canvas.bind("<Left>", self._prev_frame)
        self.canvas.bind("<Right>", self._next_frame)
        self.canvas.bind("<Down>", self._prev_entity)
        self.canvas.bind("<Up>", self._next_entity)
        self.canvas.bind("<space>", self._toggle_play)

    def _on_resize(self, event):
        self.canvas_center = Vector(event.width / 2, event.height / 2)
        self._update()

    def _prev_frame(self, event=None):
        self.frame = max(0, self.frame - 1)
        self._update()

    def _next_frame(self, event=None):
        self.frame += 1
        self._update()

    def _prev_entity(self, event=None):
        self.focused_entity = (self.focused_entity - 1) % len(self.entities)
        self._update()

    def _next_entity(self, event=None):
        self.focused_entity = (self.focused_entity + 1) % len(self.entities)
        self._update()

    def _toggle_play(self, event=None):
        self.playing = not self.playing

    def _tick(self):
        if self.playing:
            self._next_frame()
        self.root.after(25, self._tick)

    def _update(self):
        frame_entities = self.engine.get_frame(self.frame)
        if frame_entities is None:
            self.root.quit()
        else:
            self._redraw(frame_entities)

    def _redraw(self, entities):
        self.current_draw_index = 0
        self._adjust_camera(entities)
        for line in self.lines:
            self._draw_line(line)
        for entity in entities:
            self._draw_entity(entity)
        self._draw_text(entities)

    def _adjust_camera(self, entities):
        entity = entities[self.focused_entity]
        avg_x = sum(p.position.x for p in entity.points) / len(entity.points)
        avg_y = sum(p.position.y for p in entity.points) / len(entity.points)
        self.origin = Vector(avg_x, avg_y)

    def _physics_to_canvas(self, v: Vector) -> Vector:
        return self.canvas_center + self.ZOOM * (v - self.origin)

    def _draw_entity(self, entity: Entity):
        mv_len_zoom = self.MV_LENGTH * self.ZOOM

        for bone in entity.bones:
            if isinstance(bone, NormalBone):
                color = "blue"
            elif isinstance(bone, FragileBone) and entity.state == EntityState.MOUNTED:
                color = "red"
            elif isinstance(bone, RepelBone):
                color = "pink"
            else:
                continue

            p1 = self._physics_to_canvas(bone.base.point1.position)
            p2 = self._physics_to_canvas(bone.base.point2.position)
            self._generate_line(self.BONE_WIDTH, p1, p2, color=color)

        for point in entity.points:
            pos = self._physics_to_canvas(point.position)
            vel_unit = point.velocity.unit()
            tail = pos + mv_len_zoom * vel_unit
            self._generate_line(self.MV_WIDTH, pos, tail, color=self.MV_COLOR)
            self._generate_circle(pos.x, pos.y, self.CP_RADIUS, color=self.CP_COLOR)

    def _draw_line(self, line: PhysicsLine):
        p1, p2 = line.endpoints
        if line.flipped:
            p1, p2 = p2, p1

        ext_amount = line.length * line.ext_ratio
        hitbox_vec = line.normal_unit * (LINE_HITBOX_HEIGHT / 2)

        c_p1 = self._physics_to_canvas(p1)
        c_p2 = self._physics_to_canvas(p2)
        left_ext = self._physics_to_canvas(p1 - ext_amount * line.unit)
        right_ext = self._physics_to_canvas(p2 + ext_amount * line.unit)
        gwell_p1 = self._physics_to_canvas(p1 + hitbox_vec)
        gwell_p2 = self._physics_to_canvas(p2 + hitbox_vec)

        if line.left_ext:
            self._generate_line(self.EXTENSION_DRAW_WIDTH, c_p1, left_ext, color="red")
        if line.right_ext:
            self._generate_line(self.EXTENSION_DRAW_WIDTH, c_p2, right_ext, color="red")

        self._generate_line(LINE_HITBOX_HEIGHT, gwell_p1, gwell_p2, color="gray")

        line_color = "red" if line.acceleration != 0 else "blue"
        self._generate_line(
            self.LINE_DRAW_WIDTH, c_p1, c_p2, round_cap=True, color=line_color
        )

    def _draw_text(self, entities):
        minutes = int(self.frame / (60 * FRAMES_PER_SECOND))
        seconds = str(100 + int((self.frame / FRAMES_PER_SECOND) % 60))[1:]
        frames = str(100 + self.frame % FRAMES_PER_SECOND)[1:]
        timestamp = f"{minutes}:{seconds}:{frames}"

        self._generate_text(
            timestamp, self.canvas_center.x, self.canvas_center.y * 2 - 50
        )
        self._generate_text(
            f"Entity {self.focused_entity}",
            self.canvas_center.x,
            self.canvas_center.y * 2 - 25,
        )

        for i, point in enumerate(entities[self.focused_entity].points):
            self._generate_text(f"{point.position}", 10, i * 25 + 25)

    def _generate_line(
        self, width: float, p1: Vector, p2: Vector, color="black", round_cap=False
    ):
        if self.current_draw_index == len(self.canvas_cache):
            line_obj = self.canvas.create_line(0, 0, 0, 0)
            self.canvas.itemconfig(
                line_obj,
                width=width * self.ZOOM,
                capstyle="round" if round_cap else "butt",
                fill=color,
            )
            self.canvas_cache.append(line_obj)
        else:
            line_obj = self.canvas_cache[self.current_draw_index]

        self.canvas.coords(line_obj, p1.x, p1.y, p2.x, p2.y)
        self.current_draw_index += 1

    def _generate_circle(self, x: float, y: float, radius: float, color="black"):
        if self.current_draw_index == len(self.canvas_cache):
            circle = self.canvas.create_oval(0, 0, 0, 0, fill=color)
            self.canvas_cache.append(circle)
        else:
            circle = self.canvas_cache[self.current_draw_index]

        self.canvas.coords(circle, x - radius, y - radius, x + radius, y + radius)
        self.current_draw_index += 1

    def _generate_text(self, text: str, x: float, y: float):
        if self.current_draw_index == len(self.canvas_cache):
            text_obj = self.canvas.create_text(
                x, y, font=("Helvetica", 12), fill="black", anchor="w"
            )
            self.canvas_cache.append(text_obj)
        else:
            text_obj = self.canvas_cache[self.current_draw_index]

        self.canvas.itemconfig(text_obj, text=text)
        self.current_draw_index += 1


if __name__ == "__main__":
    TrackSimulator("fixtures/feature_legacy_test.track.json")
