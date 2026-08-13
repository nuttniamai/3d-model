"""แหวนรอง / บูช / ปลอกรองระยะ (spacer) — ชิ้นที่ต้องปริ้นบ่อยที่สุดในบ้าน

    python parts/spacer.py --inner-dia 8 --outer-dia 16 --height 5
inner_dia คือขนาด "แกนจริง" ที่จะสอด — โปรแกรมเผื่อค่าหด FDM ให้อัตโนมัติ
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build123d import Align, Cylinder, Pos, chamfer
from partkit import fdm

# ---- พารามิเตอร์ (mm) ----
PARAMS = dict(
    inner_dia=8.0,    # ขนาดแกน/สกรูจริงที่จะสอด
    outer_dia=16.0,   # เส้นผ่านศูนย์กลางนอก
    height=5.0,       # ความสูง
    fit="slide",      # การสวม: press / tight / slide / loose
    chamfer_c=0.6,    # ลบคมปากรูและขอบนอก (0 = ไม่ลบ)
)

FITS = dict(press=fdm.FIT_PRESS, tight=fdm.FIT_TIGHT,
            slide=fdm.FIT_SLIDE, loose=fdm.FIT_LOOSE)


def build(p):
    bore = fdm.hole_dia(p["inner_dia"], FITS[str(p["fit"]).lower()])
    if p["outer_dia"] - bore < 2 * fdm.MIN_WALL:
        raise ValueError(
            f"ผนังบางเกินไป: outer_dia ต้อง >= {bore + 2 * fdm.MIN_WALL:.1f} mm")

    body = Cylinder(p["outer_dia"] / 2, p["height"],
                    align=(Align.CENTER, Align.CENTER, Align.MIN))
    hole = Pos(0, 0, -0.5) * Cylinder(bore / 2, p["height"] + 1,
                                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    part = body - hole

    if p["chamfer_c"] > 0:
        part = chamfer(part.edges(), min(p["chamfer_c"], p["height"] / 3))
    return part


if __name__ == "__main__":
    from partkit.cli import run_cli
    run_cli(build, PARAMS, "spacer")
