from main import get_moment
import tkinter as tk
import json
from convert import convert_lines, convert_riders

target_track = "line_flags"

track = json.load(open(f"fixtures/{target_track}.track.json", "r"))
riders = convert_riders(track["riders"])
lines = convert_lines(track["lines"])

focused_rider = 0
frame = 0
iteration = 0
subiteration = 0

root = tk.Tk()
root.title("Line Rider Python Engine")
canvas = tk.Canvas(root, width=1280, height=720, bg="white")
canvas.pack()

# ball = canvas.create_oval(180, 180, 220, 220, fill="red")


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
    print(focused_rider, frame, iteration, subiteration)
    # entities = get_moment(2, frame, iteration, subiteration, riders, lines)
    # print(entities)
    # canvas.move(ball, x_change, y_change)


canvas.bind("<Left>", prev_frame)
canvas.bind("<Right>", next_frame)
canvas.bind("<Down>", prev_rider)
canvas.bind("<Up>", next_rider)
canvas.bind("<Alt-Left>", prev_iteration)
canvas.bind("<Alt-Right>", next_iteration)
canvas.bind("<Shift-Left>", prev_subiteration)
canvas.bind("<Shift-Right>", next_subiteration)

canvas.focus_set()
root.mainloop()
