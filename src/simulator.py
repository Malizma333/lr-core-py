# Opens a track file in a read-only simulator

TARGET_TRACK = "fixtures/line_flags.track.json"
ZOOM = 12

from engine.engine import Engine, FRAMES_PER_SECOND
from engine.vector import Vector
from engine.entity import Entity, EntityState, NormalBone, MountBone, RepelBone
from engine.line import PhysicsLine, MAX_LINE_EXTENSION_RATIO, LINE_HITBOX_HEIGHT
from utils.convert import convert_lines, convert_entities, convert_version
import tkinter as tk
import json
import decimal

__builtins__.float = lambda x: decimal.Decimal(str(x))

track = json.load(open(TARGET_TRACK, "r"))
version = convert_version(track["version"])
entities = convert_entities(track["riders"])
lines = convert_lines(track["lines"])
engine = Engine(version, entities, lines)

focused_entity = 0
frame = 0
playing = False

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


def prev_entity(event):
    global focused_entity
    focused_entity = (focused_entity - 1) % len(entities)
    update()


def next_entity(event):
    global focused_entity
    focused_entity = (focused_entity + 1) % len(entities)
    update()


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

    draw_text(entities)


def adjust_camera(entities: list[Entity]):
    global origin
    new_origin = Vector(0, 0)
    for point in entities[focused_entity].points:
        new_origin += point.position
    origin = new_origin / len(entities[focused_entity].points)


def physics_to_canvas(v: Vector) -> Vector:
    return canvas_center + ZOOM * (v - origin)


def draw_entity(i: int, entity: Entity):
    CP_RADIUS = 0.25
    BONE_WIDTH = 0.25
    MV_LENGTH = 3
    MV_WIDTH = 0.25
    MV_COLOR = "green"
    CP_COLOR = "white"

    mv_len_zoom = MV_LENGTH * ZOOM
    cp_radius_zoom = CP_RADIUS * ZOOM

    for index, bone in enumerate(entity.bones):
        if type(bone) == NormalBone:
            color = "blue"
        elif type(bone) == MountBone and entity.state == EntityState.MOUNTED:
            color = "red"
        elif type(bone) == RepelBone:
            color = "pink"
        else:
            continue

        c_bone_p1 = physics_to_canvas(bone.base.point1.position)
        c_bone_p2 = physics_to_canvas(bone.base.point2.position)

        bone_id = f"entities_{i}_bones_{index}"
        bone_object = canvas_cache.get(bone_id)

        if bone_object is None:
            bone_object = canvas.create_line(
                0, 0, 0, 0, width=BONE_WIDTH * ZOOM, fill=color
            )
            canvas_cache[bone_id] = bone_object
        else:
            canvas.itemconfig(bone_object, fill=color)

        canvas.coords(bone_object, c_bone_p1.x, c_bone_p1.y, c_bone_p2.x, c_bone_p2.y)

    for index, point in enumerate(entity.points):
        c_cp_pos = physics_to_canvas(point.position)
        velocity_unit = point.velocity.unit()
        c_mv_tail = Vector(
            c_cp_pos.x + mv_len_zoom * velocity_unit.x,
            c_cp_pos.y + mv_len_zoom * velocity_unit.y,
        )
        cp_bounds_offset = Vector(cp_radius_zoom, cp_radius_zoom)
        bound_tl = c_cp_pos - cp_bounds_offset
        bound_br = c_cp_pos + cp_bounds_offset

        mv_id = f"entities_{i}_vectors_{index}"
        mv_line = canvas_cache.get(mv_id)

        if mv_line is None:
            mv_line = canvas.create_line(
                0, 0, 0, 0, width=MV_WIDTH * ZOOM, fill=MV_COLOR
            )
            canvas_cache[mv_id] = mv_line

        canvas.coords(mv_line, c_cp_pos.x, c_cp_pos.y, c_mv_tail.x, c_mv_tail.y)

        cp_id = f"entities_{i}_points_{index}"
        cp_oval = canvas_cache.get(cp_id)

        if cp_oval is None:
            cp_oval = canvas.create_oval(0, 0, 0, 0, fill=CP_COLOR)
            canvas_cache[cp_id] = cp_oval

        canvas.coords(cp_oval, bound_tl.x, bound_tl.y, bound_br.x, bound_br.y)


def draw_line(i: int, line: PhysicsLine):
    EXTENSION_DRAW_WIDTH = 1
    LINE_DRAW_WIDTH = 2

    point1, point2 = line.endpoints

    if line.flipped:
        point1, point2 = point2, point1

    ext_amount = line.length * line.ext_ratio
    hitbox_vec = line.normal_unit * (LINE_HITBOX_HEIGHT / 2)

    c_line_p1 = physics_to_canvas(point1)
    c_line_p2 = physics_to_canvas(point2)
    c_left_ext = physics_to_canvas(point1 - ext_amount * line.unit)
    c_right_ext = physics_to_canvas(point2 + ext_amount * line.unit)
    c_gwell_p1 = physics_to_canvas(point1 + hitbox_vec)
    c_gwell_p2 = physics_to_canvas(point2 + hitbox_vec)

    if line.left_ext:
        id = f"lines_{i}_left_ext"
        obj = canvas_cache.get(id)
        if obj is None:
            obj = canvas.create_line(
                0, 0, 0, 0, width=EXTENSION_DRAW_WIDTH * ZOOM, fill="red"
            )
            canvas_cache[id] = obj
        canvas.coords(obj, c_line_p1.x, c_line_p1.y, c_left_ext.x, c_left_ext.y)

    if line.right_ext:
        id = f"lines_{i}_right_ext"
        obj = canvas_cache.get(id)
        if obj is None:
            obj = canvas.create_line(
                0, 0, 0, 0, width=EXTENSION_DRAW_WIDTH * ZOOM, fill="red"
            )
            canvas_cache[id] = obj
        canvas.coords(obj, c_line_p2.x, c_line_p2.y, c_right_ext.x, c_right_ext.y)

    gwell_id = f"lines_{i}_gwell"
    gwell = canvas_cache.get(gwell_id)
    if gwell is None:
        gwell = canvas.create_line(
            0, 0, 0, 0, width=LINE_HITBOX_HEIGHT * ZOOM, fill="gray"
        )
        canvas_cache[gwell_id] = gwell
    canvas.coords(gwell, c_gwell_p1.x, c_gwell_p1.y, c_gwell_p2.x, c_gwell_p2.y)

    line_id = f"lines_{i}"
    line_obj = canvas_cache.get(line_id)
    if line_obj is None:
        line_obj = canvas.create_line(
            0, 0, 0, 0, width=LINE_DRAW_WIDTH * ZOOM, capstyle="round"
        )
        canvas_cache[line_id] = line_obj
    canvas.coords(line_obj, c_line_p1.x, c_line_p1.y, c_line_p2.x, c_line_p2.y)


def draw_text(entities: list[Entity]):
    minutes = int(frame / (60 * FRAMES_PER_SECOND))
    seconds = str(100 + int((frame / FRAMES_PER_SECOND) % 60))[1:]
    frames = str(100 + frame % FRAMES_PER_SECOND)[1:]
    timestamp = f"{minutes}:{seconds}:{frames}"

    text_object = canvas_cache.setdefault(
        "current_moment_text",
        canvas.create_text(
            canvas_center.x,
            canvas_center.y * 2 - 50,
            font=("Helvetica", 12),
            fill="black",
        ),
    )
    canvas.itemconfig(text_object, text=timestamp)

    text_object = canvas_cache.setdefault(
        "current_rider_text",
        canvas.create_text(
            canvas_center.x,
            canvas_center.y * 2 - 25,
            font=("Helvetica", 12),
            fill="black",
        ),
    )
    canvas.itemconfig(text_object, text=f"Entity {focused_entity}")

    for i, point in enumerate(entities[focused_entity].points):
        text_object = canvas_cache.setdefault(
            f"current_entity_coord_{i}",
            canvas.create_text(
                10, i * 25 + 25, font=("Helvetica", 12), fill="black", anchor="w"
            ),
        )
        canvas.itemconfig(text_object, text=f"{point.position}")


def tick():
    if playing:
        next_frame(event=None)
    root.after(25, tick)


def toggle_player(event):
    global playing
    playing = not playing


# Keybinds
canvas.bind("<Left>", prev_frame)
canvas.bind("<Right>", next_frame)
canvas.bind("<Down>", prev_entity)
canvas.bind("<Up>", next_entity)
canvas.bind("<space>", toggle_player)

update()
tick()

canvas.focus_set()
root.mainloop()
