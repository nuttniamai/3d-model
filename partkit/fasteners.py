"""Helper สร้าง "รูสกรู/ช่องน็อต" สำหรับสกรูเมตริก M2–M8

ทุกฟังก์ชันคืนค่าเป็นก้อน solid (build123d Part) ที่หันปาก "ลง" ตามแกน -Z
โดยผิวบนของรูอยู่ที่ระนาบ Z=0 — นำไปวางด้วย Pos(x, y, z) แล้ว "ลบ" ออกจากชิ้นงาน:

    part -= Pos(10, 0, top_z) * clearance_hole("M4", depth=8)

ข้อมูลอ้างอิงมาตรฐาน ISO 273 (รูสวมสกรู), DIN 912 (หัวจม), DIN 934 (น็อตหกเหลี่ยม)
บวกค่าชดเชย FDM จาก partkit.fdm แล้วเรียบร้อย
"""
from build123d import Cylinder, Cone, Pos, Rot, RegularPolygon, extrude, Align

from . import fdm

# ตารางขนาดสกรูเมตริก (mm)
#   clearance: รูสวมแบบพอดี (ISO 273 fine/medium)
#   tap:       รูสำหรับสกรูเกลียวปล่อยกัดเนื้อพลาสติกเอง
#   head_dia / head_h: หัวจม socket cap (DIN 912)
#   cs_dia:    หัวเตเปอร์ countersunk 90° (DIN 7991)
#   nut_flats / nut_h: น็อตหกเหลี่ยม (DIN 934) ระยะขอบขนาน / ความหนา
#   insert_dia / insert_len: ช่องฝัง heat-set insert (ขนาดที่นิยมในวงการ 3D print)
METRIC = {
    "M2":   dict(clearance=2.4, tap=1.7,  head_dia=3.8,  head_h=2.0, cs_dia=4.4,
                 nut_flats=4.0,  nut_h=1.6, insert_dia=3.2, insert_len=4.0),
    "M2.5": dict(clearance=2.9, tap=2.1,  head_dia=4.5,  head_h=2.5, cs_dia=5.5,
                 nut_flats=5.0,  nut_h=2.0, insert_dia=3.5, insert_len=5.0),
    "M3":   dict(clearance=3.4, tap=2.6,  head_dia=5.5,  head_h=3.0, cs_dia=6.3,
                 nut_flats=5.5,  nut_h=2.4, insert_dia=4.0, insert_len=5.7),
    "M4":   dict(clearance=4.5, tap=3.4,  head_dia=7.0,  head_h=4.0, cs_dia=8.4,
                 nut_flats=7.0,  nut_h=3.2, insert_dia=5.6, insert_len=8.1),
    "M5":   dict(clearance=5.5, tap=4.3,  head_dia=8.5,  head_h=5.0, cs_dia=10.4,
                 nut_flats=8.0,  nut_h=4.0, insert_dia=6.4, insert_len=9.5),
    "M6":   dict(clearance=6.6, tap=5.2,  head_dia=10.0, head_h=6.0, cs_dia=12.6,
                 nut_flats=10.0, nut_h=5.0, insert_dia=8.0, insert_len=12.7),
    "M8":   dict(clearance=9.0, tap=7.0,  head_dia=13.0, head_h=8.0, cs_dia=17.3,
                 nut_flats=13.0, nut_h=6.5, insert_dia=10.0, insert_len=12.7),
}


def _spec(size: str) -> dict:
    key = size.upper().replace(" ", "")
    if key not in METRIC:
        raise ValueError(f"ไม่รู้จักขนาดสกรู '{size}' (รองรับ: {', '.join(METRIC)})")
    return METRIC[key]


def _rod(dia: float, depth: float):
    """แท่งทรงกระบอกผิวบนอยู่ที่ Z=0 ยาวลงไปตาม -Z"""
    return Pos(0, 0, -depth / 2) * Cylinder(dia / 2, depth)


def clearance_hole(size: str, depth: float):
    """รูสวมสกรูแบบทะลุ/ไม่ทะลุ (สกรูหมุนฟรี ขันเข้าน็อตหรือ insert อีกฝั่ง)"""
    s = _spec(size)
    return _rod(s["clearance"] + fdm.HOLE_COMP, depth)


def tap_hole(size: str, depth: float):
    """รูให้สกรูกัดเกลียวเนื้อพลาสติกเอง (งานถอดเข้าออกไม่บ่อย)"""
    s = _spec(size)
    return _rod(s["tap"] + fdm.HOLE_COMP / 2, depth)


def counterbore_hole(size: str, depth: float, head_depth: float | None = None):
    """รูสวม + ช่องฝังหัวจม socket cap ให้หัวเรียบเสมอผิว"""
    s = _spec(size)
    hd = head_depth if head_depth is not None else s["head_h"] + 0.4
    hole = _rod(s["clearance"] + fdm.HOLE_COMP, depth)
    pocket = _rod(s["head_dia"] + fdm.HOLE_COMP + 2 * fdm.FIT_SLIDE, hd)
    return hole + pocket


def countersunk_hole(size: str, depth: float):
    """รูสวม + ปากบานเตเปอร์ 90° สำหรับสกรูหัวเรียบ (flat head)"""
    s = _spec(size)
    top_d = s["cs_dia"] + fdm.HOLE_COMP
    bot_d = s["clearance"] + fdm.HOLE_COMP
    cs_h = (top_d - bot_d) / 2  # มุมรวม 90° -> ลึกเท่ารัศมีส่วนต่าง
    hole = _rod(bot_d, depth)
    # Cone ใน build123d: radius ล่าง->บน, วางให้ปากกว้างอยู่ที่ Z=0
    taper = Pos(0, 0, -cs_h / 2) * Cone(bot_d / 2, top_d / 2, cs_h)
    return hole + taper


def hex_nut_pocket(size: str, depth: float | None = None):
    """ช่องหกเหลี่ยมฝังน็อต (กันหมุน) ปากช่องอยู่ที่ Z=0 ลึกลง -Z"""
    s = _spec(size)
    d = depth if depth is not None else s["nut_h"] + 0.4
    flats = s["nut_flats"] + fdm.HOLE_COMP + 2 * fdm.FIT_TIGHT
    # RegularPolygon ใช้รัศมีวงกลมล้อม (across corners) = flats / cos(30°)
    circum_r = (flats / 2) / 0.8660254
    hexagon = RegularPolygon(circum_r, 6)
    return Pos(0, 0, -d) * extrude(hexagon, d)


def heat_set_pocket(size: str, extra_depth: float = 1.0):
    """ช่องฝัง heat-set insert (ใช้หัวแร้งกดฝัง) ปากช่องที่ Z=0"""
    s = _spec(size)
    return _rod(s["insert_dia"], s["insert_len"] + extra_depth)
