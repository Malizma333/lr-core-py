import struct

breakpoint_calls_received = 0
breakpoint_target = 0
breakpoint_name = ""


def to_raw_hex(f: float):
    return f"0x{struct.unpack('>Q', struct.pack('>d', f))[0]:016x}"


def inc_breakpoints_target():
    global breakpoint_target, breakpoint_calls_received
    breakpoint_target += 1
    breakpoint_calls_received = 0


def dec_breakpoints_target():
    global breakpoint_target, breakpoint_calls_received
    breakpoint_target = max(breakpoint_target - 1, 0)
    breakpoint_calls_received = 0


def at_breakpoint(new_breakpoint_name: str | None):
    global breakpoint_target, breakpoint_calls_received, breakpoint_name
    if breakpoint_target == 0:
        return False
    if new_breakpoint_name != None:
        breakpoint_name = new_breakpoint_name
        breakpoint_calls_received += 1
    return breakpoint_calls_received >= breakpoint_target
