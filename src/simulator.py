# Opens a track file in a read-only simulator

TARGET_TRACK = "fixtures/line_flags.track.json"
ZOOM = 12

from engine.engine import (
    Engine,
    LINE_HITBOX_HEIGHT,
    FRAMES_PER_SECOND,
)
from engine.vector import Vector
from engine.entity import Entity, EntityState, NormalBone, MountBone, RepelBone
from engine.line import PhysicsLine, MAX_LINE_EXTENSION_RATIO
from utils.convert import convert_lines, convert_riders, convert_version
import tkinter as tk
import json

track = json.load(open(TARGET_TRACK, "r"))
version = convert_version(track["version"])
riders = convert_riders(track["riders"])
lines = convert_lines(track["lines"])
engine = Engine(version, riders, lines)

focused_rider = 0
frame = 0

root = tk.Tk()
root.title("Line Rider Python Engine")
canvas = tk.Canvas(root, width=1280, height=720, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)
canvas_cache = {}
canvas_center = Vector(int(canvas["width"]) / 2, int(canvas["height"]) / 2)
origin = Vector(0, 0)


def on_resize(event: tk.Event) -> None:
    global canvas_center
    canvas_center = Vector(event.width / 2, event.height / 2)
    update()


root.bind("<Configure>", on_resize)


def prev_frame(event):
    global frame
    frame = max(0, frame - 1)
    update()


def next_frame(event):
    global frame
    frame += 1
    update()


def prev_rider(event):
    global focused_rider
    focused_rider = (focused_rider - 1) % len(riders)
    update()


def next_rider(event):
    global focused_rider
    focused_rider = (focused_rider + 1) % len(riders)
    update()


# Keybinds
canvas.bind("<Left>", prev_frame)
canvas.bind("<Right>", next_frame)
canvas.bind("<Down>", prev_rider)
canvas.bind("<Up>", next_rider)


def update():
    entities = engine.get_frame(frame)

    if entities == None:
        root.quit()
        return

    redraw(entities)


def redraw(entities: list[Entity]):
    adjust_camera(entities)

    for i, line in enumerate(lines):
        draw_line(i, line)

    for i, entity in enumerate(entities):
        draw_entity(i, entity)

    draw_text()


def adjust_camera(entities: list[Entity]):
    global origin
    new_origin = Vector(0, 0)
    for point in entities[focused_rider].points:
        new_origin += point.position
    origin = new_origin / len(entities[focused_rider].points)


def physics_to_canvas(v: Vector) -> Vector:
    return canvas_center + ZOOM * (v - origin)


def draw_entity(i: int, entity: Entity):
    CP_RADIUS = 0.25
    BONE_WIDTH = 0.25
    MV_LENGTH = 3
    MV_WIDTH = 0.25
    MV_COLOR = "green"
    CP_COLOR = "white"

    for index, bone in enumerate(entity.bones):
        color = ""
        if type(bone) == NormalBone:
            color = "blue"
        elif type(bone) == MountBone and entity.state == EntityState.MOUNTED:
            color = "red"
        elif type(bone) == RepelBone:
            color = "pink"

        canvas_bone_point1 = physics_to_canvas(bone.base.point1.position)
        canvas_bone_point2 = physics_to_canvas(bone.base.point2.position)

        bone_object = canvas_cache.setdefault(
            f"entities_{i}_bones_{index}",
            canvas.create_line(0, 0, 0, 0, width=BONE_WIDTH * ZOOM, fill=color),
        )
        canvas.coords(
            bone_object,
            canvas_bone_point1.x,
            canvas_bone_point1.y,
            canvas_bone_point2.x,
            canvas_bone_point2.y,
        )

    for index, point in enumerate(entity.points):
        point_pos = point.position

        canvas_point_pos = physics_to_canvas(point_pos)
        canvas_mv_tail = canvas_point_pos + MV_LENGTH * ZOOM * point.velocity.unit()
        cp_bounds_offset = ZOOM * Vector(CP_RADIUS, CP_RADIUS)
        canvas_point_bounds = (
            canvas_point_pos - cp_bounds_offset,
            canvas_point_pos + cp_bounds_offset,
        )

        mv_object = canvas_cache.setdefault(
            f"entities_{i}_vectors_{index}",
            canvas.create_line(0, 0, 0, 0, width=MV_WIDTH * ZOOM, fill=MV_COLOR),
        )
        canvas.coords(
            mv_object,
            canvas_point_pos.x,
            canvas_point_pos.y,
            canvas_mv_tail.x,
            canvas_mv_tail.y,
        )

        cp_object = canvas_cache.setdefault(
            f"entities_{i}_points_{index}",
            canvas.create_oval(0, 0, 0, 0, fill=CP_COLOR),
        )
        canvas.coords(
            cp_object,
            canvas_point_bounds[0].x,
            canvas_point_bounds[0].y,
            canvas_point_bounds[1].x,
            canvas_point_bounds[1].y,
        )


def draw_line(i: int, line: PhysicsLine):
    EXTENSION_DRAW_WIDTH = 1
    LINE_DRAW_WIDTH = 2

    point1 = line.endpoints[0]
    point2 = line.endpoints[1]

    if line.flipped:
        point1, point2 = point2, point1

    ext_amount = line.length * min(
        MAX_LINE_EXTENSION_RATIO, LINE_HITBOX_HEIGHT / line.length
    )
    hitbox_vec = line.normal_unit * LINE_HITBOX_HEIGHT / 2

    canvas_point1 = physics_to_canvas(point1)
    canvas_point2 = physics_to_canvas(point2)
    canvas_left_ext = physics_to_canvas(point1 - ext_amount * line.unit)
    canvas_right_ext = physics_to_canvas(point2 + ext_amount * line.unit)
    canvas_gwell_point1 = physics_to_canvas(point1 + hitbox_vec)
    canvas_gwell_point2 = physics_to_canvas(point2 + hitbox_vec)

    if line.left_ext:
        line_left_ext_object = canvas_cache.setdefault(
            f"lines_{i}_left_ext",
            canvas.create_line(
                0, 0, 0, 0, width=EXTENSION_DRAW_WIDTH * ZOOM, fill="red"
            ),
        )
        canvas.coords(
            line_left_ext_object,
            canvas_point1.x,
            canvas_point1.y,
            canvas_left_ext.x,
            canvas_left_ext.y,
        )

    if line.right_ext:
        line_right_ext_object = canvas_cache.setdefault(
            f"lines_{i}_right_ext",
            canvas.create_line(
                0, 0, 0, 0, width=EXTENSION_DRAW_WIDTH * ZOOM, fill="red"
            ),
        )
        canvas.coords(
            line_right_ext_object,
            canvas_point2.x,
            canvas_point2.y,
            canvas_right_ext.x,
            canvas_right_ext.y,
        )

    line_gwell_object = canvas_cache.setdefault(
        f"lines_{i}_gwell",
        canvas.create_line(0, 0, 0, 0, width=LINE_HITBOX_HEIGHT * ZOOM, fill="gray"),
    )
    canvas.coords(
        line_gwell_object,
        canvas_gwell_point1.x,
        canvas_gwell_point1.y,
        canvas_gwell_point2.x,
        canvas_gwell_point2.y,
    )

    line_object = canvas_cache.setdefault(
        f"lines_{i}",
        canvas.create_line(0, 0, 0, 0, width=LINE_DRAW_WIDTH * ZOOM, capstyle="round"),
    )
    canvas.coords(
        line_object, canvas_point1.x, canvas_point1.y, canvas_point2.x, canvas_point2.y
    )


def draw_text():
    minutes = int(frame / (60 * FRAMES_PER_SECOND))
    seconds = str(100 + int((frame / FRAMES_PER_SECOND) % 60))[1:]
    frames = str(100 + frame % FRAMES_PER_SECOND)[1:]
    timestamp = f"{minutes}:{seconds}:{frames}"

    text_object = canvas_cache.setdefault(
        "current_moment_text",
        canvas.create_text(0, 0, font=("Helvetica", 12), fill="black"),
    )
    canvas.itemconfig(text_object, text=timestamp)
    canvas.coords(text_object, canvas_center.x, canvas_center.y * 2 - 50)

    text_object = canvas_cache.setdefault(
        "current_rider_text",
        canvas.create_text(0, 0, font=("Helvetica", 12), fill="black"),
    )
    canvas.itemconfig(text_object, text=f"Rider {focused_rider}")
    canvas.coords(text_object, canvas_center.x, canvas_center.y * 2 - 25)


update()
canvas.focus_set()
root.mainloop()
