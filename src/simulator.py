# Opens a track file in a read-only simulator

TARGET_TRACK = "fixtures/line_flags.track.json"
ZOOM = 12

from engine.engine import Engine, FRAMES_PER_SECOND
from engine.vector import Vector
from engine.entity import Entity, EntityState, NormalBone, MountBone, RepelBone
from engine.line import PhysicsLine, LINE_HITBOX_HEIGHT
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


root = tk.Tk()
root.title("Line Rider Python Engine")
canvas = tk.Canvas(root, width=1280, height=720, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)
canvas_cache = []
canvas_center = Vector(int(canvas["width"]) / 2, int(canvas["height"]) / 2)
origin = Vector(0, 0)
current_draw_index = 0
focused_entity = 0
frame = 0
playing = False


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
    global current_draw_index
    current_draw_index = 0

    adjust_camera(entities)

    for line in lines:
        draw_line(line)

    for entity in entities:
        draw_entity(entity)

    draw_text(entities)


def adjust_camera(entities: list[Entity]):
    global origin
    new_origin_x = 0
    new_origin_y = 0
    for point in entities[focused_entity].points:
        new_origin_x += point.position.x
        new_origin_y += point.position.y
    num_points = len(entities[focused_entity].points)
    origin = Vector(new_origin_x / num_points, new_origin_y / num_points)


def physics_to_canvas(v: Vector) -> Vector:
    return canvas_center + ZOOM * (v - origin)


def draw_entity(entity: Entity):
    CP_RADIUS = 2
    BONE_WIDTH = 0.25
    MV_LENGTH = 3
    MV_WIDTH = 0.25
    MV_COLOR = "green"
    CP_COLOR = "white"

    mv_len_zoom = MV_LENGTH * ZOOM

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

        generate_line(BONE_WIDTH, c_bone_p1, c_bone_p2, color=color)

    for index, point in enumerate(entity.points):
        c_cp_pos = physics_to_canvas(point.position)
        velocity_unit = point.velocity.unit()
        c_mv_tail = Vector(
            c_cp_pos.x + mv_len_zoom * velocity_unit.x,
            c_cp_pos.y + mv_len_zoom * velocity_unit.y,
        )

        generate_line(MV_WIDTH, c_cp_pos, c_mv_tail, color=MV_COLOR)
        generate_circle(c_cp_pos.x, c_cp_pos.y, CP_RADIUS, color=CP_COLOR)


def draw_line(line: PhysicsLine):
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
        generate_line(EXTENSION_DRAW_WIDTH, c_line_p1, c_left_ext, color="red")

    if line.right_ext:
        generate_line(EXTENSION_DRAW_WIDTH, c_line_p2, c_right_ext, color="red")

    generate_line(LINE_HITBOX_HEIGHT, c_gwell_p1, c_gwell_p2, color="gray")
    generate_line(LINE_DRAW_WIDTH, c_line_p1, c_line_p2, round_cap=True)


def draw_text(entities: list[Entity]):
    minutes = int(frame / (60 * FRAMES_PER_SECOND))
    seconds = str(100 + int((frame / FRAMES_PER_SECOND) % 60))[1:]
    frames = str(100 + frame % FRAMES_PER_SECOND)[1:]
    timestamp = f"{minutes}:{seconds}:{frames}"

    generate_text(timestamp, canvas_center.x, canvas_center.y * 2 - 50)
    generate_text(f"Entity {focused_entity}", canvas_center.x, canvas_center.y * 2 - 25)

    for i, point in enumerate(entities[focused_entity].points):
        generate_text(f"{point.position}", 10, i * 25 + 25)


def generate_line(width: float, p1: Vector, p2: Vector, color="black", round_cap=False):
    global current_draw_index

    if current_draw_index == len(canvas_cache):
        line_obj = canvas.create_line(0, 0, 0, 0)
        canvas.itemconfig(
            line_obj,
            width=width * ZOOM,
            capstyle="round" if round_cap else "butt",
            fill=color,
        )
        canvas_cache.append(line_obj)
    else:
        line_obj = canvas_cache[current_draw_index]

    canvas.coords(line_obj, p1.x, p1.y, p2.x, p2.y)

    current_draw_index += 1


def generate_circle(pos_x: float, pos_y: float, radius: float, color="black"):
    global current_draw_index

    if current_draw_index == len(canvas_cache):
        circle_obj = canvas.create_oval(0, 0, 0, 0, fill=color)
        canvas_cache.append(circle_obj)
    else:
        circle_obj = canvas_cache[current_draw_index]

    canvas.coords(
        circle_obj, pos_x - radius, pos_y - radius, pos_x + radius, pos_y + radius
    )

    current_draw_index += 1


def generate_text(text: str, x: float, y: float):
    global current_draw_index

    if current_draw_index == len(canvas_cache):
        text_object = canvas.create_text(
            x, y, font=("Helvetica", 12), fill="black", anchor="w"
        )
        canvas_cache.append(text_object)
    else:
        text_object = canvas_cache[current_draw_index]

    canvas.itemconfig(text_object, text=text)

    current_draw_index += 1


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
