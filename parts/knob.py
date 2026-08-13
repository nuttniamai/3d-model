"""ลูกบิด/หัวหมุน สวมแกนมอเตอร์หรือแกนโพเทนชิออมิเตอร์
รองรับแกน 3 แบบ: กลม (round), แกนปาด D (d), หกเหลี่ยม (hex)

    python parts/knob.py --dia 30 --shaft d --shaft-dia 6 --flat-depth 1.5
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build123d import (Align, Axis, Box, Cylinder, Pos, RegularPolygon,
                       chamfer, extrude)
from partkit import fdm

# ---- พารามิเตอร์ (mm) ----
PARAMS = dict(
    dia=30.0,         # เส้นผ่านศูนย์กลางลูกบิด
    height=15.0,      # ความสูง
    shaft="d",        # ชนิดแกน: round / d / hex
    shaft_dia=6.0,    # ขนาดแกนจริง (hex = ระยะขอบขนาน across flats)
    flat_depth=1.5,   # (เฉพาะแกน d) ความลึกรอยปาดจากผิวแกน
    shaft_depth=12.0, # ความลึกรูสวมแกน (เจาะจากด้านล่าง ไม่ทะลุ)
    scallops=7,       # จำนวนร่องนิ้วรอบตัว (0 = ผิวเรียบ)
    chamfer_c=1.0,    # ลบคมขอบบน
)


def _shaft_bore(p):
    """รูสวมแกน เผื่อ FIT_TIGHT ให้จับแกนแน่นพอไม่หมุนฟรี"""
    d = fdm.hole_dia(p["shaft_dia"], fdm.FIT_TIGHT)
    depth = p["shaft_depth"] + 0.5
    kind = str(p["shaft"]).lower()
    if kind == "hex":
        circum_r = (d / 2) / math.cos(math.pi / 6)
        return Pos(0, 0, -0.5) * extrude(RegularPolygon(circum_r, 6), depth)
    bore = Pos(0, 0, -0.5) * Cylinder(d / 2, depth,
                                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    if kind == "d":
        # ระยะจากศูนย์กลางถึงระนาบปาด (คงสัดส่วนรอยปาดของแกนจริง)
        flat_x = d / 2 - p["flat_depth"]
        cut = Pos(flat_x, 0, -0.5) * Box(d, d * 2, depth,
                                         align=(Align.MIN, Align.CENTER, Align.MIN))
        bore -= cut
    return bore


def build(p):
    r, h = p["dia"] / 2, p["height"]
    body = Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # ร่องนิ้วรอบตัว: หักลบทรงกระบอกเล็กเรียงเป็นวง
    n = int(p["scallops"])
    if n > 0:
        sc_r = p["dia"] * 0.12
        ring_r = r + sc_r * 0.55
        for i in range(n):
            a = 2 * math.pi * i / n
            body -= Pos(ring_r * math.cos(a), ring_r * math.sin(a), -0.5) * Cylinder(
                sc_r, h + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))

    if p["chamfer_c"] > 0:
        top = body.edges().group_by(Axis.Z)[-1]
        body = chamfer(top, min(p["chamfer_c"], h / 4))

    body -= _shaft_bore(p)
    return body


if __name__ == "__main__":
    from partkit.cli import run_cli
    run_cli(build, PARAMS, "knob")
