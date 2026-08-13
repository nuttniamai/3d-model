"""ขายึดฉากรูปตัว L — ยึดชั้นวาง กล่อง อุปกรณ์เข้ากับผนัง/โครง

แก้ตัวเลขใน PARAMS แล้วรัน:
    python parts/bracket_L.py
หรือ override ผ่าน CLI:
    python parts/bracket_L.py --leg-a 60 --thickness 5 --screw M5
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build123d import Align, Axis, Box, Pos, Rot, fillet
from partkit import countersunk_hole

# ---- พารามิเตอร์ (mm) ----
PARAMS = dict(
    leg_a=50.0,        # ความยาวขาแนวนอน
    leg_b=50.0,        # ความสูงขาแนวตั้ง
    width=20.0,        # ความกว้างขายึด
    thickness=4.0,     # ความหนาเนื้อ
    screw="M4",        # ขนาดสกรู (M2–M8)
    holes_per_leg=2,   # จำนวนรูต่อขา
    fillet_r=4.0,      # รัศมีโค้งมุมใน (เพิ่มความแข็งแรง)
)


def build(p):
    t = p["thickness"]
    a, b, w = p["leg_a"], p["leg_b"], p["width"]
    n = int(p["holes_per_leg"])

    base = Box(a, w, t, align=(Align.MIN, Align.CENTER, Align.MIN))
    wall = Box(t, w, b, align=(Align.MIN, Align.CENTER, Align.MIN))
    part = base + wall

    # โค้งมุมในตรงข้อพับ เพิ่มความแข็งแรงจุดรับแรงสูงสุด
    inner = [e for e in part.edges().filter_by(Axis.Y)
             if abs(e.center().X - t) < 1e-6 and abs(e.center().Z - t) < 1e-6]
    if inner and p["fillet_r"] > 0:
        part = fillet(inner, min(p["fillet_r"], min(a, b) - t - 0.1))

    # รูสกรูขาแนวนอน (หัวจมเรียบผิวบน เจาะลง -Z)
    usable_a = a - t - p["fillet_r"]
    for i in range(n):
        x = t + p["fillet_r"] + usable_a * (i + 1) / (n + 1)
        part -= Pos(x, 0, t) * countersunk_hole(p["screw"], t + 1)

    # รูสกรูขาแนวตั้ง (หัวจมฝั่งใน เจาะทะลุไปหาผนัง -X)
    usable_b = b - t - p["fillet_r"]
    for i in range(n):
        z = t + p["fillet_r"] + usable_b * (i + 1) / (n + 1)
        part -= Pos(t, 0, z) * Rot(0, 90, 0) * countersunk_hole(p["screw"], t + 1)

    return part


if __name__ == "__main__":
    from partkit.cli import run_cli
    run_cli(build, PARAMS, "bracket_L")
