# Opens a track file in a read-only simulator

TARGET_TRACK = "fixtures/line_flags.track.json"
ZOOM = 6

from engine import (
    get_moment,
    LINE_EXTENSION_RATIO,
    MAX_SUBIT_MOMENTUM,
    NUM_ITERATIONS,
    MAX_SUBIT,
    LINE_HITBOX_HEIGHT,
)
from convert import convert_lines, convert_riders, convert_version
from lrtypes import Entity, PhysicsLine
import tkinter as tk
import json

track = json.load(open(TARGET_TRACK, "r"))
riders = convert_riders(track["riders"])
lines = convert_lines(track["lines"])
version = convert_version(track["version"])

focused_rider = 0
frame = -1
iteration = 0
subiteration = 0

root = tk.Tk()
root.title("Line Rider Python Engine")
canvas = tk.Canvas(root, width=1280, height=720, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)
canvas_cache = {}
canvas_center = (int(canvas["width"]) / 2, int(canvas["height"]) / 2)
origin = (0, 0)


def on_resize(event: tk.Event) -> None:
    global canvas_center
    canvas_center = (event.width / 2, event.height / 2)
    update()


root.bind("<Configure>", on_resize)


def prev_subiteration(event):
    global frame, iteration, subiteration
    if frame == -1:
        pass
    elif subiteration == 0:
        if iteration == 0:
            frame -= 1
            iteration = NUM_ITERATIONS
            subiteration = MAX_SUBIT
        elif iteration == 1:
            iteration -= 1
            subiteration = MAX_SUBIT_MOMENTUM
        else:
            iteration -= 1
            subiteration = MAX_SUBIT
    else:
        subiteration -= 1

    update()


def next_subiteration(event):
    global frame, iteration, subiteration
    if iteration == 0:
        if subiteration == MAX_SUBIT_MOMENTUM:
            subiteration = 0
            iteration += 1
        else:
            subiteration += 1
    else:
        if subiteration == MAX_SUBIT:
            if iteration == NUM_ITERATIONS:
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
    if frame == -1:
        pass
    elif iteration == 0:
        frame -= 1
        iteration = NUM_ITERATIONS
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
    iteration = NUM_ITERATIONS
    subiteration = MAX_SUBIT
    frame = max(-1, frame - 1)
    update()


def next_frame(event):
    global frame, iteration, subiteration
    iteration = NUM_ITERATIONS
    subiteration = MAX_SUBIT
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


canvas.bind("<Left>", prev_frame)
canvas.bind("<Right>", next_frame)
canvas.bind("<Down>", prev_rider)
canvas.bind("<Up>", next_rider)
canvas.bind("<Alt-Left>", prev_iteration)
canvas.bind("<Alt-Right>", next_iteration)
canvas.bind("<Control-Left>", prev_subiteration)
canvas.bind("<Control-Right>", next_subiteration)


def update():
    entities = get_moment(version, frame, iteration, subiteration, riders, lines)

    if entities == None:
        print("Moment returned none")
        root.quit()
        return

    adjust_camera(entities)

    for i, line in enumerate(lines):
        draw_line(i, line)

    for i, entity in enumerate(entities):
        draw_entity(i, entity)

    draw_text()


def adjust_camera(entities: list[Entity]):
    global origin
    new_origin = [0.0, 0.0]
    for point in entities[focused_rider]["points"]:
        new_origin[0] += point["x"]
        new_origin[1] += point["y"]
    new_origin[0] /= len(entities[focused_rider]["points"])
    new_origin[1] /= len(entities[focused_rider]["points"])
    origin = (new_origin[0], new_origin[1])


def physics_to_canvas(x: float, y: float) -> tuple[float, float]:
    return (
        (x - origin[0]) * ZOOM + canvas_center[0],
        (y - origin[1]) * ZOOM + canvas_center[1],
    )


def draw_entity(i: int, entity: Entity):
    cp_radius = 1 * ZOOM
    offset = cp_radius / 2

    for index, bone in enumerate(entity["bones"]):
        p1 = entity["points"][bone["POINT1"]]
        p2 = entity["points"][bone["POINT2"]]
        (x1, y1) = physics_to_canvas(p1["x"], p1["y"])
        (x2, y2) = physics_to_canvas(p2["x"], p2["y"])
        bone_object = canvas_cache.setdefault(
            f"entities_{i}_bones_{index}",
            canvas.create_line(0, 0, 0, 0, width=0.25 * ZOOM, fill="pink"),
        )
        canvas.coords(bone_object, x1 + offset, y1 + offset, x2 + offset, y2 + offset)

    for index, point in enumerate(entity["points"]):
        (x, y) = physics_to_canvas(point["x"], point["y"])
        magnitude = (point["dx"] ** 2 + point["dy"] ** 2) ** 0.5
        unit = (point["dx"] / magnitude, point["dy"] / magnitude)
        mv_object = canvas_cache.setdefault(
            f"entities_{i}_vectors_{index}",
            canvas.create_line(0, 0, 0, 0, width=0.25 * ZOOM, fill="red"),
        )
        canvas.coords(
            mv_object,
            x + offset,
            y + offset,
            x + 10 * unit[0] + offset,
            y + 10 * unit[1] + offset,
        )
        cp_object = canvas_cache.setdefault(
            f"entities_{i}_points_{index}", canvas.create_oval(0, 0, 0, 0, fill="cyan")
        )
        canvas.coords(cp_object, x, y, x + cp_radius, y + cp_radius)


def draw_line(i: int, line: PhysicsLine):
    (x1, y1) = (line["X1"], line["Y1"])
    (x2, y2) = (line["X2"], line["Y2"])

    if line["FLIPPED"]:
        (x1, y1, x2, y2) = (x2, y2, x1, y1)

    delta = (x2 - x1, y2 - y1)
    magnitude = (delta[0] ** 2 + delta[1] ** 2) ** 0.5
    unit = (delta[0] / magnitude, delta[1] / magnitude)
    ext_amount = min(40, magnitude) * LINE_EXTENSION_RATIO

    if line["LEFT_EXTENSION"]:
        line_left_ext_object = canvas_cache.setdefault(
            f"lines_{i}_left_ext",
            canvas.create_line(0, 0, 0, 0, width=1 * ZOOM, fill="red"),
        )
        lx1, ly1 = physics_to_canvas(
            x1 - ext_amount * unit[0], y1 - ext_amount * unit[1]
        )
        lx2, ly2 = physics_to_canvas(x1, y1)
        canvas.coords(line_left_ext_object, lx1, ly1, lx2, ly2)

    if line["RIGHT_EXTENSION"]:
        line_right_ext_object = canvas_cache.setdefault(
            f"lines_{i}_right_ext",
            canvas.create_line(0, 0, 0, 0, width=1 * ZOOM, fill="red"),
        )
        lx1, ly1 = physics_to_canvas(x2, y2)
        lx2, ly2 = physics_to_canvas(
            x2 + ext_amount * unit[0], y2 + ext_amount * unit[1]
        )
        canvas.coords(line_right_ext_object, lx1, ly1, lx2, ly2)

    line_gwell_object = canvas_cache.setdefault(
        f"lines_{i}_gwell",
        canvas.create_line(0, 0, 0, 0, width=LINE_HITBOX_HEIGHT * ZOOM, fill="gray"),
    )
    lx1, ly1 = physics_to_canvas(x1 - 5 * unit[1], y1 + 5 * unit[0])
    lx2, ly2 = physics_to_canvas(x2 - 5 * unit[1], y2 + 5 * unit[0])
    canvas.coords(line_gwell_object, lx1, ly1, lx2, ly2)

    line_object = canvas_cache.setdefault(
        f"lines_{i}", canvas.create_line(0, 0, 0, 0, width=2 * ZOOM, capstyle="round")
    )
    lx1, ly1 = physics_to_canvas(x1, y1)
    lx2, ly2 = physics_to_canvas(x2, y2)
    canvas.coords(line_object, lx1, ly1, lx2, ly2)


def draw_text():
    if frame == -1:
        timestamp = "0:00:00"
    else:
        minutes = int(frame / 2400)
        seconds = str(100 + int((frame / 40) % 60))[1:]
        frames = str(100 + (frame + 1) % 40)[1:]
        timestamp = f"{minutes}:{seconds}:{frames}"

        if not (iteration == 6 and subiteration == 22):
            timestamp += f"_I{iteration}"
        if not (
            iteration == 0
            and subiteration == 3
            or iteration != 0
            and subiteration == 22
        ):
            timestamp += f"_S{subiteration}"

    text_object = canvas_cache.setdefault(
        "current_moment_text",
        canvas.create_text(0, 0, font=("Helvetica", 12), fill="black"),
    )
    canvas.itemconfig(text_object, text=timestamp)
    canvas.coords(text_object, canvas_center[0], canvas_center[1] * 2 - 50)

    text_object = canvas_cache.setdefault(
        "current_rider_text",
        canvas.create_text(0, 0, font=("Helvetica", 12), fill="black"),
    )
    canvas.itemconfig(text_object, text=f"Rider {focused_rider}")
    canvas.coords(text_object, canvas_center[0], canvas_center[1] * 2 - 25)


update()
canvas.focus_set()
root.mainloop()
