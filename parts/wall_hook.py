"""ตะขอแขวนผนังรูปตัว J — แขวนสายไฟ หูฟัง เครื่องมือ

    python parts/wall_hook.py --arm-len 40 --width 15
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build123d import Align, Axis, Box, Pos, Rot, fillet
from partkit import countersunk_hole

# ---- พารามิเตอร์ (mm) ----
PARAMS = dict(
    plate_w=25.0,     # ความกว้างแผ่นยึดผนัง
    plate_h=60.0,     # ความสูงแผ่นยึดผนัง
    plate_t=4.0,      # ความหนาแผ่น
    arm_len=35.0,     # ความยาวแขนตะขอที่ยื่นออกมา
    arm_t=6.0,        # ความหนาแขน
    lip_h=15.0,       # ความสูงปลายตะขอที่งอนขึ้น
    width=15.0,       # ความกว้างของแขน/ปลายตะขอ
    screw="M4",       # สกรูยึดผนัง
    fillet_r=6.0,     # โค้งข้อต่อแขน-แผ่น (จุดรับแรง)
)


def build(p):
    t, w = p["plate_t"], p["width"]

    plate = Box(t, p["plate_w"], p["plate_h"],
                align=(Align.MIN, Align.CENTER, Align.MIN))
    arm = Box(t + p["arm_len"], w, p["arm_t"],
              align=(Align.MIN, Align.CENTER, Align.MIN))
    lip = Pos(t + p["arm_len"] - p["arm_t"], 0, 0) * Box(
        p["arm_t"], w, p["lip_h"], align=(Align.MIN, Align.CENTER, Align.MIN))
    part = plate + arm + lip

    # โค้งรอยต่อบนของแขนกับแผ่น (รับแรงดึงมากสุดตอนมีของแขวน)
    joint = [e for e in part.edges().filter_by(Axis.Y)
             if abs(e.center().X - t) < 1e-6 and abs(e.center().Z - p["arm_t"]) < 1e-6]
    if joint and p["fillet_r"] > 0:
        part = fillet(joint, min(p["fillet_r"], p["arm_len"] / 3))

    # โค้งมุมในของง่ามตะขอ (ระหว่างแขนกับปลายงอน)
    crook = [e for e in part.edges().filter_by(Axis.Y)
             if abs(e.center().X - (t + p["arm_len"] - p["arm_t"])) < 1e-6
             and abs(e.center().Z - p["arm_t"]) < 1e-6]
    if crook:
        part = fillet(crook, min(2.0, p["arm_len"] / 6))

    # รูสกรู 2 รู บน-ล่างของแผ่น หัวจมฝั่งหน้า เจาะเข้าหาผนัง (-X)
    margin = max(8.0, p["plate_w"] / 3)
    for z in (p["plate_h"] - margin, p["arm_t"] + margin):
        part -= Pos(t, 0, z) * Rot(0, 90, 0) * countersunk_hole(p["screw"], t + 1)

    return part


if __name__ == "__main__":
    from partkit.cli import run_cli
    run_cli(build, PARAMS, "wall_hook")
