"""กล่องพร้อมฝาสวม — ระบุ "ขนาดภายใน" ตรงกับของที่จะใส่ แล้วโปรแกรมคิดผนัง
และค่าเผื่อฝาให้เอง (ฝาสวมแบบ slide fit ถอดง่ายไม่โยก)

    python parts/box_with_lid.py --inner-l 80 --inner-w 50 --inner-d 30
ได้ 2 ไฟล์: box_with_lid_box.* และ box_with_lid_lid.*
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build123d import Align, Axis, Box, Pos, fillet
from partkit import fdm

# ---- พารามิเตอร์ (mm) ----
PARAMS = dict(
    inner_l=80.0,    # ความยาวภายใน
    inner_w=50.0,    # ความกว้างภายใน
    inner_d=30.0,    # ความลึกภายใน
    wall=2.0,        # ความหนาผนัง
    bottom_t=2.0,    # ความหนาก้น
    lid_t=2.4,       # ความหนาแผ่นฝา
    lip_h=6.0,       # ความสูงขอบฝาที่สอดลงในกล่อง
    corner_r=3.0,    # รัศมีโค้งมุมนอก
)


def _rounded(part, r):
    if r > 0:
        part = fillet(part.edges().filter_by(Axis.Z), r)
    return part


def build(p):
    il, iw, idp = p["inner_l"], p["inner_w"], p["inner_d"]
    wall, bt = p["wall"], p["bottom_t"]
    if wall < fdm.MIN_WALL:
        raise ValueError(f"ผนังต้องหนาอย่างน้อย {fdm.MIN_WALL} mm")

    # ---- กล่อง ----
    outer = Box(il + 2 * wall, iw + 2 * wall, idp + bt,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
    outer = _rounded(outer, p["corner_r"])
    cavity = Pos(0, 0, bt) * Box(il, iw, idp + 1,
                                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    cavity = _rounded(cavity, max(p["corner_r"] - wall, 0.5))
    box = outer - cavity

    # ---- ฝา: แผ่นปิดเต็มขนาดนอก + ขอบสอดลงช่องกล่องแบบมี clearance ----
    c = fdm.FIT_SLIDE  # ช่องว่างต่อด้านระหว่างขอบฝากับผนังใน
    plate = Box(il + 2 * wall, iw + 2 * wall, p["lid_t"],
                align=(Align.CENTER, Align.CENTER, Align.MIN))
    plate = _rounded(plate, p["corner_r"])
    lip_l, lip_w = il - 2 * c, iw - 2 * c
    lip_outer = Pos(0, 0, p["lid_t"]) * Box(
        lip_l, lip_w, p["lip_h"], align=(Align.CENTER, Align.CENTER, Align.MIN))
    lip_outer = _rounded(lip_outer, max(p["corner_r"] - wall - c, 0.5))
    lip_inner = Pos(0, 0, p["lid_t"]) * Box(
        lip_l - 2 * wall, lip_w - 2 * wall, p["lip_h"] + 1,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    lid = plate + (lip_outer - lip_inner)

    return {"box": box, "lid": lid}


if __name__ == "__main__":
    from partkit.cli import run_cli
    run_cli(build, PARAMS, "box_with_lid")
