# Opens a track file in a read-only simulator

TARGET_TRACK = "fixtures/line_flags.track.json"
ZOOM = 4

from engine import get_moment, LINE_EXTENSION_RATIO
from convert import convert_lines, convert_riders, convert_version
from lrtypes import Entity, PhysicsLine, NormalBone, RepelBone, MountBone
import tkinter as tk
import json

track = json.load(open(TARGET_TRACK, "r"))
riders = convert_riders(track["riders"])
lines = convert_lines(track["lines"])
version = convert_version(track["version"])

focused_rider = 0
frame = 0
iteration = 0
subiteration = 0

root = tk.Tk()
root.title("Line Rider Python Engine")
canvas = tk.Canvas(root, width=1280, height=720, bg="white")
canvas.pack()
canvas_cache = {}
CANVAS_CENTER = (int(canvas["width"]) / 2, int(canvas["height"]) / 2)


def physics_to_canvas(x: float, y: float) -> tuple[float, float]:
    return (x * ZOOM + CANVAS_CENTER[0], y * ZOOM + CANVAS_CENTER[1])


def prev_subiteration(event):
    global frame, iteration, subiteration
    if subiteration == 0:
        if iteration == 0:
            if frame == 0:
                pass
            else:
                frame -= 1
                iteration = 6
                subiteration = 22
        elif iteration == 1:
            iteration -= 1
            subiteration = 3
        else:
            iteration -= 1
            subiteration = 22
    else:
        subiteration -= 1

    update()


def next_subiteration(event):
    global frame, iteration, subiteration
    if iteration == 0:
        if subiteration == 3:
            subiteration = 0
            iteration += 1
        else:
            subiteration += 1
    else:
        if subiteration == 22:
            if iteration == 6:
                subiteration = 0
                iteration = 0
                frame += 1
            else:
                subiteration = 0
                iteration += 1
        else:
            subiteration += 1
    update()


def prev_iteration(event):
    global frame, iteration, subiteration
    subiteration = 0
    if iteration == 0:
        if frame == 0:
            pass
        else:
            frame -= 1
            iteration = 6
    else:
        iteration -= 1

    update()


def next_iteration(event):
    global frame, iteration, subiteration
    subiteration = 0
    if iteration == 6:
        iteration = 0
        frame += 1
    else:
        iteration += 1
    update()


def prev_frame(event):
    global frame, iteration, subiteration
    iteration = 0
    subiteration = 0
    frame = max(0, frame - 1)
    update()


def next_frame(event):
    global frame, iteration, subiteration
    iteration = 0
    subiteration = 0
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


def update():
    entities = get_moment(version, frame, iteration, subiteration, riders, lines)

    if entities == None:
        print("Moment returned none")
        root.quit()
        return

    for i, entity in enumerate(entities):
        draw_entity(i, entity)

    for i, line in enumerate(lines):
        draw_line(i, line)


def draw_entity(i: int, entity: Entity):
    for index, bone in enumerate(entity["bones"]):
        p1 = entity["points"][bone["POINT1"]]
        p2 = entity["points"][bone["POINT2"]]
        (x1, y1) = physics_to_canvas(p1["x"], p1["y"])
        (x2, y2) = physics_to_canvas(p2["x"], p2["y"])
        bone_object = canvas_cache.get(
            f"entities_{i}_bones_{index}",
            canvas.create_line(0, 0, 0, 0, width=2, fill="pink"),
        )
        canvas.coords(bone_object, x1, y1, x2, y2)

    for index, point in entity["points"].items():
        (x, y) = physics_to_canvas(point["x"], point["y"])
        cp_radius = 3
        magnitude = (point["dx"] ** 2 + point["dy"] ** 2) ** 0.5
        unit = (point["dx"] / magnitude, point["dy"] / magnitude)
        mv_object = canvas_cache.get(
            f"entities_{i}_vectors_{index}",
            canvas.create_line(0, 0, 0, 0, width=2, fill="red"),
        )
        canvas.coords(
            mv_object,
            x + cp_radius / 2,
            y + cp_radius / 2,
            x + 10 * unit[0] + cp_radius / 2,
            y + 10 * unit[1] + cp_radius / 2,
        )
        cp_object = canvas_cache.get(
            f"entities_{i}_points_{index}", canvas.create_oval(0, 0, 0, 0, fill="cyan")
        )
        canvas.coords(cp_object, x, y, x + cp_radius, y + cp_radius)


def draw_line(i: int, line: PhysicsLine):
    (x1, y1) = physics_to_canvas(line["X1"], line["Y1"])
    (x2, y2) = physics_to_canvas(line["X2"], line["Y2"])
    if line["FLIPPED"]:
        (x1, y1, x2, y2) = (x2, y2, x1, y1)

    delta = (x2 - x1, y2 - y1)
    magnitude = (delta[0] ** 2 + delta[1] ** 2) ** 0.5
    unit = (delta[0] / magnitude, delta[1] / magnitude)
    if line["LEFT_EXTENSION"]:
        line_left_ext_object = canvas_cache.get(
            f"lines_{i}_left_ext", canvas.create_line(0, 0, 0, 0, width=2, fill="red")
        )
        canvas.coords(
            line_left_ext_object,
            x1 - magnitude * LINE_EXTENSION_RATIO * unit[0],
            y1 - magnitude * LINE_EXTENSION_RATIO * unit[1],
            x1,
            y1,
        )
    if line["RIGHT_EXTENSION"]:
        line_right_ext_object = canvas_cache.get(
            f"lines_{i}_left_ext", canvas.create_line(0, 0, 0, 0, width=2, fill="red")
        )
        canvas.coords(
            line_right_ext_object,
            x1,
            y1,
            x1 + magnitude * LINE_EXTENSION_RATIO * unit[0],
            y1 + magnitude * LINE_EXTENSION_RATIO * unit[1],
        )
    line_gwell_object = canvas_cache.get(
        f"lines_{i}_gwell", canvas.create_line(0, 0, 0, 0, width=20, fill="gray")
    )
    canvas.coords(
        line_gwell_object,
        x1 - 10 * unit[1],
        y1 + 10 * unit[0],
        x2 - 10 * unit[1],
        y2 + 10 * unit[0],
    )
    line_object = canvas_cache.get(
        f"lines_{i}", canvas.create_line(0, 0, 0, 0, width=4, capstyle="round")
    )
    canvas.coords(line_object, x1, y1, x2, y2)


canvas.bind("<Left>", prev_frame)
canvas.bind("<Right>", next_frame)
canvas.bind("<Down>", prev_rider)
canvas.bind("<Up>", next_rider)
canvas.bind("<Alt-Left>", prev_iteration)
canvas.bind("<Alt-Right>", next_iteration)
canvas.bind("<Shift-Left>", prev_subiteration)
canvas.bind("<Shift-Right>", next_subiteration)

update()

canvas.focus_set()
root.mainloop()
