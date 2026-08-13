"""โครงในลำโพง JBL Flip 4 — เปลือกทรงกระบอกผนังบาง มีปลอกยึด passive radiator สองข้าง

อะไหล่แท้: รหัส 55-FLP4H1-0UHB1 "Rubber front casing JBL Flip 4"
วัสดุเดิม PC+TPU (โครง PC แข็ง หุ้มยาง TPU) — งานปริ้นทดแทนแนะนำ PETG

โครงสร้างจริง (วัดจากไฟล์ STL ต้นฉบับด้วย trimesh — แกน X = แนวยาวลำโพง):
- ทั้งชิ้นคือ "ท่อผนังบาง" รัศมีนอก ~30.5 mm ที่ถูกเฉือนออกเกือบหมด เหลือ
  1) ปลอกเต็มวงสองปลาย (ยึด passive radiator)
  2) สายคาดใต้ท้อง กว้าง ±30° ผนังหนาแค่ 1.0 mm เชื่อมปลอกสองข้าง
  3) ช่วงบานที่สายคาดค่อย ๆ กว้างขึ้นจนกลืนเข้าปลอก
- สายคาดเจาะ: รูใหญ่ Ø10.5 สองรู, รูจิ๋ว Ø1.75 ห้ารูเรียงกัน (ช่องระบายอากาศ),
  สลอตยาว 45.5x14.25 ฝั่งขวา, รูกลม Ø13.5 บนช่วงบานฝั่งซ้าย

*** สำคัญ: สายคาดเป็นผิวโค้ง ไม่ใช่แผ่นแบน และบางเพียง 1 mm ***

หมายเหตุเรื่องแนว z: ในไฟล์ต้นฉบับทั้งสายคาดและรูทุกรูเยื้องจากแกนทรงกระบอก
ราว 0.65-1.2 mm และเยื้องไม่เท่ากันแต่ละรู (-0.45 ถึง -1.20) ซึ่งเป็นผลจาก
mesh ที่หยาบ/เอียงเล็กน้อย ไม่ใช่แบบจริง — ค่า *_z จึงตั้งเป็น 0 ทั้งหมด
= รูทุกรูอยู่กึ่งกลางความกว้างสายคาดพอดี ถ้าวัดของจริงแล้วพบว่าเยื้องจริง
ค่อยตั้ง --holes-z / --vent-z / --slot-z / --hole3-z ทีหลังได้
ค่าปลอก/ช่วงบานเป็นค่าประมาณ เพราะ mesh ต้นฉบับหยาบมาก (3998 หน้า ไม่ปิดสนิท)
ส่วนสายคาดและตำแหน่งรูวัดได้แม่น ใช้ทาบเทียบกับของจริงได้

    python parts/dual_ring_bar.py                    # ทั้งชิ้น
    python parts/dual_ring_bar.py --section flat     # สายคาดคลี่แบน (ทดสอบตำแหน่งรู - เร็วสุด)
    python parts/dual_ring_bar.py --section strap    # สายคาดโค้งจริง
    python parts/dual_ring_bar.py --section sleeve   # เฉพาะปลอก (ทดสอบความพอดีรูสวม)
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build123d import (Align, Box, Circle, Cone, Cylinder, Plane, Polygon, Pos,
                       Rot, SlotOverall, extrude, loft, make_face)
from partkit import fdm

# ---- พารามิเตอร์ (mm / องศา) — วัดจากไฟล์ต้นฉบับ ----
PARAMS = dict(
    length=170.3,      # ความยาวรวมทั้งชิ้น
    r_out=30.5,        # รัศมีนอกของเปลือกทรงกระบอก
    wall=1.0,          # ความหนาผนังสายคาด (วัดได้ 1.00 สม่ำเสมอ)
    strap_ang=30.0,    # ครึ่งมุมความกว้างสายคาด (±30° จากก้น)
    flare_x=58.0,      # |x| ที่สายคาดเริ่มบานออก
    flare_ang=90.0,    # ครึ่งมุมตอนจบการบาน (ก่อนกลืนเข้าปลอก)
    ring_x=74.0,       # |x| ที่ปลอกเต็มวงเริ่ม
    ring_od_in=60.8,   # Ø นอกปลอก ด้านที่ติดสายคาด
    ring_od_out=56.4,  # Ø นอกปลอก ที่ปลายสุด (ผิวนอกเรียวเล็กน้อย)
    ring_seat=44.8,    # Ø บ่ารองด้านใน (แคบสุด อยู่ปลายในของปลอก)
    ring_bore=54.2,    # Ø รูสวม passive radiator (ช่วงทรงกระบอกปลายนอก)
    ring_bore_x=81.0,  # |x| ที่กรวยด้านในเปิดจนถึงขนาดรูสวมพอดี
    fit="none",        # "none" = ตามไฟล์เดิมเป๊ะ
                       # press/tight/slide/loose = ตีความ ring_bore เป็นขนาด
                       # ชิ้นจริงที่จะสวม แล้วเผื่อค่าหด FDM ให้อัตโนมัติ
    hole1_dia=10.5,    # รูใหญ่ลดน้ำหนัก (0 = ไม่เจาะ)
    hole1_x=-38.0,
    hole2_dia=10.5,
    hole2_x=-7.25,
    holes_z=0.0,       # ระดับ z ร่วมของรูใหญ่ทั้งสอง (0 = กลางความกว้างสายคาด)
    vent_n=5,          # รูจิ๋วระบายอากาศเรียงแถว (0 = ไม่เจาะ)
    vent_dia=1.75,
    vent_pitch=2.2,
    vent_x=-23.45,     # ศูนย์กลางของแถว
    vent_z=0.0,
    slot_l=45.5,       # สลอตยาว (0 = ไม่เจาะ)
    slot_w=14.25,
    slot_x=36.2,
    slot_z=0.0,
    hole3_dia=13.5,    # รูกลมบนช่วงบานฝั่งซ้าย (0 = ไม่เจาะ)
    hole3_x=-65.0,
    hole3_z=0.0,
    section="full",    # full | flat | strap | sleeve — เลือกส่วนที่จะสร้าง
    flat_t=1.0,        # ความหนาชิ้นแบนทดสอบ (เท่าผนังจริง ประหยัดเส้น)
    flat_margin=3.0,   # เนื้อขอบที่เหลือรอบช่องนอกสุดของชิ้นแบน
)

FITS = dict(press=fdm.FIT_PRESS, tight=fdm.FIT_TIGHT,
            slide=fdm.FIT_SLIDE, loose=fdm.FIT_LOOSE)


def _bore_dia(p):
    f = str(p["fit"]).lower()
    if f in ("none", ""):
        return p["ring_bore"]
    return fdm.hole_dia(p["ring_bore"], FITS[f])


def _sector_face(p, half_ang, x):
    """หน้าตัดสายคาด: วงแหวนบางเฉือนเหลือช่วงมุม ±half_ang รอบทิศ -Y ที่ตำแหน่ง x

    sketch อยู่บนระนาบ YZ (พิกัด local u=global Y, v=global Z) แล้ว extrude ไปตาม X
    """
    plane = Plane.YZ.offset(x)
    ring = Circle(p["r_out"]) - Circle(p["r_out"] - p["wall"])
    a = math.radians(half_ang)
    reach = p["r_out"] * 1.5
    n = max(8, int(half_ang / 3))
    pts = [(0.0, 0.0)]
    for i in range(n + 1):
        t = -a + 2 * a * i / n
        pts.append((-reach * math.cos(t), reach * math.sin(t)))
    wedge = make_face(Polygon(*pts, align=None).wire())
    return plane * (ring & wedge)


def _sleeve(p, bore, side):
    """ปลอกยึด passive radiator หนึ่งข้าง

    ผิวนอก: กรวยเรียวเล็กน้อยจากด้านสายคาดไปปลายนอก (มุมถอดแม่พิมพ์)
    ผิวใน:  บ่าแคบที่ปลายใน แล้วเปิดเป็นกรวยออกจนได้ขนาดรูสวม แล้วต่อทรงกระบอก
    """
    x_end = p["length"] / 2
    L = x_end - p["ring_x"]
    L1 = min(p["ring_bore_x"] - p["ring_x"], L)
    BOT = (Align.CENTER, Align.CENTER, Align.MIN)

    body = Cone(p["ring_od_in"] / 2, p["ring_od_out"] / 2, L, align=BOT)
    body -= Cone(p["ring_seat"] / 2, bore / 2, L1, align=BOT)
    body -= Pos(0, 0, L1) * Cylinder(bore / 2, L - L1 + 1, align=BOT)

    return Pos(side * p["ring_x"], 0, 0) * Rot(0, side * 90, 0) * body


def _lay_flat(part):
    """จัดชิ้นให้อยู่กึ่งกลาง XY และก้นแตะ Z=0 (พร้อมวางเตียงปริ้น)"""
    bb = part.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * part


def _cut_features(part, p):
    """เจาะรู/สลอตทั้งหมด — ทุกช่องเจาะทะลุตามแกน Y (ทิศถอดแม่พิมพ์)

    ใช้ร่วมกันทั้งชิ้นโค้งจริงและชิ้นแบนสำหรับทดสอบ ตำแหน่งรูจึงตรงกันเสมอ
    """
    def cut_y(shape_2d, x, z):
        sk = Plane.XZ.offset(-100) * Pos(x, z, 0) * shape_2d
        return extrude(sk, 200)

    for hx, hd in ((p["hole1_x"], p["hole1_dia"]), (p["hole2_x"], p["hole2_dia"])):
        if hd > 0:
            part -= cut_y(Circle(hd / 2), hx, p["holes_z"])

    n = int(p["vent_n"])
    for i in range(n):
        vx = p["vent_x"] + (i - (n - 1) / 2) * p["vent_pitch"]
        part -= cut_y(Circle(p["vent_dia"] / 2), vx, p["vent_z"])

    if p["slot_l"] > 0:
        part -= cut_y(SlotOverall(p["slot_l"], p["slot_w"]), p["slot_x"], p["slot_z"])

    if p["hole3_dia"] > 0:
        part -= cut_y(Circle(p["hole3_dia"] / 2), p["hole3_x"], p["hole3_z"])
    return part


def _feature_span(p):
    """ขอบซ้ายสุด-ขวาสุดของทุกช่องที่เจาะ (พิกัด x)"""
    xs = []
    for hx, hd in ((p["hole1_x"], p["hole1_dia"]), (p["hole2_x"], p["hole2_dia"])):
        if hd > 0:
            xs += [hx - hd / 2, hx + hd / 2]
    n = int(p["vent_n"])
    if n > 0:
        reach = (n - 1) / 2 * p["vent_pitch"] + p["vent_dia"] / 2
        xs += [p["vent_x"] - reach, p["vent_x"] + reach]
    if p["slot_l"] > 0:
        xs += [p["slot_x"] - p["slot_l"] / 2, p["slot_x"] + p["slot_l"] / 2]
    if p["hole3_dia"] > 0:
        xs += [p["hole3_x"] - p["hole3_dia"] / 2, p["hole3_x"] + p["hole3_dia"] / 2]
    return min(xs), max(xs)


def _flat_blank(p):
    """แผ่นแบน = สายคาดที่ "คลี่" ออก วางตำแหน่งเดียวกับสายคาดจริง (หนาตามแกน Y)

    ความกว้าง = ความยาวส่วนโค้งจริง (2·r·θ) ไม่ใช่ระยะคอร์ด จึงเป็นการคลี่ที่ถูกต้อง
    ม้วนกลับรัศมี r_out เมื่อไรก็ได้รูปเดิม
    ตำแหน่งรูตามแนวยาว (X) เท่ากับของโค้งเป๊ะ ส่วนแนวขวางต่างไม่ถึง 0.001 mm
    เพราะรูทุกรูอยู่ห่างแนวกลางท้องไม่เกิน 1.2 mm

    ความยาวขยายเองให้ครอบทุกช่องเต็มรูป + เนื้อขอบ flat_margin จะได้ไม่มีช่องไหน
    ถูกตัดขาดที่ขอบชิ้น (วัดเทียบง่าย) และปรับตามพารามิเตอร์ใหม่ได้เองเสมอ
    """
    t = p["flat_t"]
    lo, hi = _feature_span(p)
    half = max(p["flare_x"], abs(lo) + p["flat_margin"], hi + p["flat_margin"])
    width = 2 * p["r_out"] * math.radians(p["strap_ang"])
    return Pos(0, -p["r_out"] + t / 2, 0) * Box(2 * half, t, width)


def _section(part, p, which):
    """ตัดเฉพาะบางส่วนมาปริ้นทดสอบ พร้อมจัดท่าวางเตียงให้แล้ว"""
    if which == "strap":
        # สายคาดช่วงที่มุมคงที่ แล้วพลิกให้โค้งนูนขึ้น (โค้งขึ้น = ไม่ต้อง support)
        keep = Box(2 * p["flare_x"], 500, 500)
        return _lay_flat(Rot(-90, 0, 0) * (part & keep))

    if which == "sleeve":
        # ปลอกขวาเต็มวง ตั้งแกนรูขึ้น (ไม่ต้อง support ใช้เช็คความพอดีรูสวม)
        x_mid = (p["ring_x"] + p["length"] / 2) / 2
        keep = Pos(x_mid, 0, 0) * Box(p["length"] / 2 - p["ring_x"], 500, 500)
        return _lay_flat(Rot(0, 90, 0) * (part & keep))

    raise ValueError(f"section ต้องเป็น full / flat / strap / sleeve (ได้ '{which}')")


def build(p):
    bore = _bore_dia(p)
    if p["ring_od_out"] - bore < 2 * fdm.MIN_WALL - 1e-6:   # เผื่อ float noise ที่ขอบพอดี
        raise ValueError(
            f"ผนังปลอกบางเกินไป: ring_od_out ต้อง >= {bore + 2 * fdm.MIN_WALL:.1f} mm")
    if p["wall"] < 0.4:
        raise ValueError("wall บางกว่าหัวฉีด 0.4 mm ปริ้นไม่ได้")

    x_end = p["length"] / 2
    if not (0 < p["flare_x"] < p["ring_x"] < x_end):
        raise ValueError("ต้องเรียงลำดับ flare_x < ring_x < length/2")

    which = str(p["section"]).lower()

    # ---- ชิ้นแบนสำหรับทดสอบตำแหน่งรู: ข้ามการสร้างส่วนโค้ง/ปลอกทั้งหมด ----
    if which == "flat":
        blank = _cut_features(_flat_blank(p), p)
        # พลิกให้ผิว "ด้านนอก" ของชิ้นจริงหงายขึ้น (เทียบกับของจริงได้ตรงด้าน)
        return {"flat": _lay_flat(Rot(-90, 0, 0) * blank)}

    # ---- สายคาดช่วงมุมคงที่ ----
    part = extrude(_sector_face(p, p["strap_ang"], -p["flare_x"]),
                   2 * p["flare_x"])

    # ---- ช่วงบาน: loft จากมุมสายคาดไปมุมที่กว้างขึ้น จนถึงขอบปลอก ----
    flares = [loft([_sector_face(p, p["strap_ang"], s * p["flare_x"]),
                    _sector_face(p, p["flare_ang"], s * p["ring_x"])])
              for s in (1, -1)]

    # ---- ปลอกเต็มวงสองข้าง ----
    rings = [_sleeve(p, bore, s) for s in (1, -1)]

    part = part.fuse(*flares, *rings, tol=1e-3)

    part = _cut_features(part, p)

    if which != "full":
        return {which: _section(part, p, which)}
    return part


if __name__ == "__main__":
    from partkit.cli import run_cli
    run_cli(build, PARAMS, "dual_ring_bar")
