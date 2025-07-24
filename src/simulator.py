import tkinter as tk
import json
from enum import Enum

from engine.engine import Engine
from engine.vector import Vector
from engine.entity import Entity, NormalBone, FragileBone, RepelBone
from engine.line import PhysicsLine
from utils.convert import convert_lines, convert_entities, convert_version


class DrawTag(Enum):
    Line = "line"
    Ext = "ext"
    Hitbox = "hitbox"
    Bone = "bone"
    Point = "point"
    Vec = "vec"
    Text = "text"


class TrackSimulator:
    DRAW_LINES = True
    START_FRAME = 0
    ZOOM = 6
    MV_LENGTH = 3
    MV_WIDTH = 0.25
    MV_COLOR = "green"
    CP_RADIUS = 2
    CP_COLOR = "white"
    BONE_WIDTH = 0.25
    EXTENSION_WIDTH = 0.5
    EXTENSION_COLOR = "red"
    LINE_WIDTH = 2
    LINE_RED_COLOR = "#fd4f38"
    LINE_BLUE_COLOR = "#3995fd"
    NORMAL_BONE_COLOR = "blue"
    FRAGILE_BONE_COLOR = "red"
    REPEL_BONE_COLOR = "magenta"
    FLUTTER_BONE_COLOR = "purple"
    HITBOX_COLOR = "lightgray"
    FPS = 40

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

        self.canvas_cache = {tag: [] for tag in DrawTag}
        self.draw_indices = {tag: 0 for tag in DrawTag}

        self.canvas_center = 0.5 * Vector(
            int(self.canvas["width"]), int(self.canvas["height"])
        )
        self.origin = Vector(0, 0)

        self.frame = self.START_FRAME
        self.focused_entity = 0
        self.playing = False
        self.drawing_line_start = None
        self.temp_line_id = None

        self._bind_keys()
        self.root.bind("<Configure>", self._on_resize)

        self._update()
        self._tick()

        self.canvas.focus_set()
        self.root.mainloop()

    def _bind_keys(self):
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<BackSpace>", self._remove_last_line)
        self.canvas.bind("<Left>", self._prev_frame)
        self.canvas.bind("<Right>", self._next_frame)
        self.canvas.bind("<Down>", self._prev_entity)
        self.canvas.bind("<Up>", self._next_entity)
        self.canvas.bind("<space>", self._toggle_play)

    def _on_mouse_down(self, event):
        self.drawing_line_start = Vector(event.x, event.y)

    def _on_mouse_drag(self, event):
        if self.drawing_line_start is not None:
            if self.temp_line_id is not None:
                self.canvas.delete(self.temp_line_id)
            self.temp_line_id = self.canvas.create_line(
                self.drawing_line_start.x,
                self.drawing_line_start.y,
                event.x,
                event.y,
                fill="black",
                width=self.LINE_WIDTH,
                dash=(4, 2),
            )

    def _on_mouse_up(self, event):
        if self.drawing_line_start is not None:
            start_canvas_point = self.drawing_line_start
            end_canvas_point = Vector(event.x, event.y)
            start_physics_point = self._canvas_to_physics(start_canvas_point)
            end_physics_point = self._canvas_to_physics(end_canvas_point)

            if start_physics_point != end_physics_point:
                new_line = PhysicsLine(
                    -1, start_physics_point, end_physics_point, False, False, False, 0
                )
                self.engine.add_line(new_line)
                self.lines.append(new_line)
                self._update()

            self.drawing_line_start = None
            if self.temp_line_id is not None:
                self.canvas.delete(self.temp_line_id)
                self.temp_line_id = None

    def _remove_last_line(self, event=None):
        if len(self.lines) > 0:
            last_line = self.lines.pop()
            self.engine.remove_line(last_line.id)
            self._update()

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
        self.root.after(int(1000 / self.FPS), self._tick)

    def _update(self):
        frame_state = self.engine.get_frame(self.frame)
        if frame_state is None:
            self.root.quit()
        else:
            for tag in DrawTag:
                self.draw_indices[tag] = 0
            self._redraw(frame_state.entities)
            self._cleanup_canvas_cache()

    def _cleanup_canvas_cache(self):
        for tag in DrawTag:
            cache = self.canvas_cache[tag]
            active = self.draw_indices[tag]
            for i in range(active, len(cache)):
                self.canvas.delete(cache[i])
            del cache[active:]

    def _redraw(self, entities: list[Entity]):
        self.origin = entities[self.focused_entity].get_average_position()
        for line in self.lines:
            if self.DRAW_LINES:
                self._draw_line(line)
        for entity in entities:
            self._draw_entity(entity)
        self._draw_text(entities)
        self.canvas.tag_raise(DrawTag.Hitbox.name)
        self.canvas.tag_raise(DrawTag.Ext.name)
        self.canvas.tag_raise(DrawTag.Line.name)
        self.canvas.tag_raise(DrawTag.Bone.name)
        self.canvas.tag_raise(DrawTag.Vec.name)
        self.canvas.tag_raise(DrawTag.Point.name)
        self.canvas.tag_raise(DrawTag.Text.name)

    def _physics_to_canvas(self, v: Vector) -> Vector:
        return self.canvas_center + self.ZOOM * (v - self.origin)

    def _canvas_to_physics(self, v: Vector) -> Vector:
        return (v - self.canvas_center) / self.ZOOM + self.origin

    def _draw_entity(self, entity: Entity):
        mv_len_zoom = self.MV_LENGTH * self.ZOOM

        for bone in entity.flutter_bones:
            p1 = self._physics_to_canvas(bone.base.point1.base.position)
            p2 = self._physics_to_canvas(bone.base.point2.base.position)
            self._generate_line(
                DrawTag.Bone, self.BONE_WIDTH, p1, p2, color=self.FLUTTER_BONE_COLOR
            )

        for bone in entity.structural_bones:
            if isinstance(bone, NormalBone):
                color = self.NORMAL_BONE_COLOR
            elif isinstance(bone, FragileBone):
                color = self.FRAGILE_BONE_COLOR
            elif isinstance(bone, RepelBone):
                color = self.REPEL_BONE_COLOR
            else:
                color = "white"

            p1 = self._physics_to_canvas(bone.base.point1.base.position)
            p2 = self._physics_to_canvas(bone.base.point2.base.position)
            self._generate_line(DrawTag.Bone, self.BONE_WIDTH, p1, p2, color=color)

        for point in entity.get_all_points():
            pos = self._physics_to_canvas(point.position)
            vel_length = point.velocity.length()
            vel_unit = Vector(0, 1)
            if vel_length != 0:
                vel_unit = point.velocity / vel_length
            tail = pos + mv_len_zoom * vel_unit
            self._generate_line(
                DrawTag.Vec, self.MV_WIDTH, pos, tail, color=self.MV_COLOR
            )
            self._generate_circle(
                DrawTag.Point, pos.x, pos.y, self.CP_RADIUS, color=self.CP_COLOR
            )

    def _draw_line(self, line: PhysicsLine):
        p1, p2 = line.endpoints
        if line.flipped:
            p1, p2 = p2, p1

        ext_amount = line.length * line.ext_ratio
        hitbox_vec = line.normal_unit * (line.HITBOX_HEIGHT / 2)

        c_p1 = self._physics_to_canvas(p1)
        c_p2 = self._physics_to_canvas(p2)
        left_ext = self._physics_to_canvas(p1 - ext_amount * line.unit)
        right_ext = self._physics_to_canvas(p2 + ext_amount * line.unit)
        gwell_p1 = self._physics_to_canvas(p1 + hitbox_vec)
        gwell_p2 = self._physics_to_canvas(p2 + hitbox_vec)

        if line.left_ext:
            self._generate_line(
                DrawTag.Ext,
                self.EXTENSION_WIDTH,
                c_p1,
                left_ext,
                color=self.EXTENSION_COLOR,
                round_cap=True,
            )
        if line.right_ext:
            self._generate_line(
                DrawTag.Ext,
                self.EXTENSION_WIDTH,
                c_p2,
                right_ext,
                color=self.EXTENSION_COLOR,
                round_cap=True,
            )

        self._generate_line(
            DrawTag.Hitbox,
            line.HITBOX_HEIGHT,
            gwell_p1,
            gwell_p2,
            color=self.HITBOX_COLOR,
        )

        line_color = (
            self.LINE_RED_COLOR if line.acceleration != 0 else self.LINE_BLUE_COLOR
        )
        self._generate_line(
            DrawTag.Line, self.LINE_WIDTH, c_p1, c_p2, round_cap=True, color=line_color
        )

    def _draw_text(self, entities: list[Entity]):
        minutes = int(self.frame / (60 * self.FPS))
        seconds = str(100 + int((self.frame / self.FPS) % 60))[1:]
        frames = str(100 + self.frame % self.FPS)[1:]
        timestamp = f"{minutes}:{seconds}:{frames}"

        self._generate_text(
            timestamp, self.canvas_center.x, self.canvas_center.y * 2 - 50
        )
        self._generate_text(
            f"Entity {self.focused_entity}",
            self.canvas_center.x,
            self.canvas_center.y * 2 - 25,
        )

        pos_strings = [
            f"{p.base.position}"
            for p in entities[self.focused_entity].structural_points
        ]
        pos_strings[6], pos_strings[7] = pos_strings[7], pos_strings[6]

        for i, pos_str in enumerate(pos_strings):
            self._generate_text(f"{pos_str}", 10, i * 25 + 25)

    def _generate_line(
        self,
        tag: DrawTag,
        width: float,
        p1: Vector,
        p2: Vector,
        color: str,
        round_cap=False,
    ):
        cache = self.canvas_cache[tag]
        index = self.draw_indices[tag]

        if index == len(cache):
            line_obj = self.canvas.create_line(0, 0, 0, 0)
            self.canvas.itemconfig(
                line_obj,
                width=width * self.ZOOM,
                capstyle="round" if round_cap else "butt",
                fill=color,
                tags=tag.name,
            )
            cache.append(line_obj)
        else:
            line_obj = cache[index]

        self.canvas.coords(line_obj, p1.x, p1.y, p2.x, p2.y)
        self.draw_indices[tag] += 1

    def _generate_circle(
        self, tag: DrawTag, x: float, y: float, radius: float, color: str
    ):
        cache = self.canvas_cache[tag]
        index = self.draw_indices[tag]

        if index == len(cache):
            circle = self.canvas.create_oval(0, 0, 0, 0, fill=color, tags=tag.name)
            cache.append(circle)
        else:
            circle = cache[index]

        self.canvas.coords(circle, x - radius, y - radius, x + radius, y + radius)
        self.draw_indices[tag] += 1

    def _generate_text(self, text: str, x: float, y: float):
        tag = DrawTag.Text
        cache = self.canvas_cache[tag]
        index = self.draw_indices[tag]

        if index == len(cache):
            text_obj = self.canvas.create_text(
                x, y, font=("Helvetica", 12), fill="black", anchor="w", tags=tag.name
            )
            cache.append(text_obj)
        else:
            text_obj = cache[index]

        self.canvas.itemconfig(text_obj, text=text)
        self.canvas.coords(text_obj, x, y)
        self.draw_indices[tag] += 1


if __name__ == "__main__":
    TrackSimulator("fixtures/dismount.track.json")
