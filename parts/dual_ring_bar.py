"""วงแหวนคู่เชื่อมด้วยคานกลาง (ทรงก้านสูบ/con-rod) — คอบานแนบวงแหวนอัตโนมัติ
พร้อมรูกลมและช่อง slot ลดน้ำหนักบนคาน

ชิ้นถูกสร้างใน "ท่านอนปริ้น": ความหนาชิ้นอยู่ตามแกน Z (รู/slot เจาะทะลุแกน Z)
วงแหวนสองข้างเอียงบานออกได้ตาม ring_tilt

โครงร่างแนวราบสร้างด้วย convex hull ระหว่างสี่เหลี่ยมคานกับวงกลมวงแหวน
ทำให้ได้เส้นบานเฉียงแนบวงพอดีทุกสัดส่วน โดยไม่มีผิวสัมผัสแบบ tangent
ที่ทำให้ boolean ของ CAD kernel เสื่อม

    python parts/dual_ring_bar.py --span 160 --ring-id 42 --ring-od 55
วัดของจริงแล้ว override ได้ทุกค่า: python parts/dual_ring_bar.py --help
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build123d import (Circle, Cylinder, GeomType, Plane, Pos, Rectangle, Rot,
                       SlotOverall, extrude, fillet, make_hull)
from partkit import fdm

# ---- พารามิเตอร์ (mm) — ค่า default กะจากสัดส่วนภาพ วัดของจริงแล้วแก้ได้เลย ----
PARAMS = dict(
    span=160.0,       # ระยะห่างศูนย์กลางวงแหวนซ้าย-ขวา
    ring_id=42.0,     # รูในวงแหวน = ขนาด "ของจริง" ที่จะสวม (เผื่อ FDM ให้อัตโนมัติ)
    ring_od=55.0,     # ขอบนอกวงแหวน
    ring_w=16.0,      # ความหนาวงแหวนตามแนวแกนรู
    ring_tilt=12.0,   # องศาที่วงแหวนเอียงบานออก (0 = ตั้งตรง)
    fit="slide",      # ความแน่นรูสวม: press / tight / slide / loose
    beam_h=30.0,      # ความสูงหน้าตัดคานกลาง (แนวราบ)
    beam_t=10.0,      # ความหนาคาน (แกน Z ทิศเจาะรู)
    neck_len=25.0,    # ระยะคานตรงก่อนเริ่มบานเข้าหาวงแหวน
    holes_n=3,        # จำนวนรูกลมลดน้ำหนัก (0 = ไม่เจาะ)
    holes_dia=12.0,   # ขนาดรูกลม
    holes_pitch=17.0, # ระยะห่างศูนย์กลางรูกลม
    holes_x=-32.0,    # ตำแหน่งศูนย์กลางกลุ่มรูกลม (ลบ = ฝั่งซ้าย)
    slot_l=45.0,      # ความยาวรวมช่อง slot (0 = ไม่เจาะ)
    slot_w=14.0,      # ความกว้างช่อง slot
    slot_x=32.0,      # ตำแหน่งศูนย์กลาง slot (บวก = ฝั่งขวา)
    edge_r=1.5,       # ลบคมขอบวงแหวน (0 = คมตรง)
)

FITS = dict(press=fdm.FIT_PRESS, tight=fdm.FIT_TIGHT,
            slide=fdm.FIT_SLIDE, loose=fdm.FIT_LOOSE)


def _bore_dia(p):
    """ขนาดรูสวมจริงหลังเผื่อค่าหด FDM และความแน่นที่เลือก"""
    return fdm.hole_dia(p["ring_id"], FITS[str(p["fit"]).lower()])


def _ring(p):
    """วงแหวนแกน Z ศูนย์กลางที่ origin ลบคมขอบแล้ว"""
    bore = _bore_dia(p)
    if p["ring_od"] - bore < 2 * fdm.MIN_WALL:
        raise ValueError(
            f"ผนังวงแหวนบางเกินไป: ring_od ต้อง >= {bore + 2 * fdm.MIN_WALL:.1f} mm")
    ring = (Cylinder(p["ring_od"] / 2, p["ring_w"])
            - Cylinder(bore / 2, p["ring_w"] + 1))
    if p["edge_r"] > 0:
        # ลบคมเฉพาะขอบนอก — ห้าม fillet ขอบรูใน เพราะผิว fillet จะสัมผัสแนบ
        # กับทรงกระบอกที่ใช้เจาะรูซ้ำใน build() ทำให้ boolean เกิด sliver
        outer = [e for e in ring.edges().filter_by(GeomType.CIRCLE)
                 if e.radius > (p["ring_od"] + bore) / 4]
        ring = fillet(outer, min(p["edge_r"], p["ring_w"] / 4))
    return ring


def _web(p, half):
    """คาน + คอบาน เป็นแผ่นหนา beam_t: hull ของสี่เหลี่ยมคานกับวงกลมใต้วงแหวน

    วงกลม hull เล็กกว่าขอบนอกวงแหวน 2 mm เพื่อให้ปลายคอ "ฝังใน" เนื้อวงแหวนเสมอ
    (แม้วงแหวนจะเอียง) — ผิวตัดกันแบบตั้งฉาก ไม่มีจุดเฉียด (tangent) ให้ kernel พัง
    """
    hull_r = p["ring_od"] / 2 - 2.0
    if hull_r < 3:
        raise ValueError("ring_od เล็กเกินไป")
    beam_half_len = half - p["ring_od"] / 2 - p["neck_len"]
    if beam_half_len <= 5:
        raise ValueError("span สั้นเกินไปเมื่อเทียบกับ ring_od + neck_len")
    rect = Rectangle(2 * beam_half_len, p["beam_h"])
    profile = None
    for s in (1, -1):
        edges = list(rect.edges()) + list((Pos(s * half, 0, 0) * Circle(hull_r)).edges())
        h = make_hull(edges)
        profile = h if profile is None else profile + h
    return extrude(profile, p["beam_t"] / 2, both=True)


def build(p):
    half = p["span"] / 2

    # ---- วงแหวน 2 ข้าง เอียงบานออก + แผ่นคาน/คอบาน ----
    ring = _ring(p)
    part = (Pos(half, 0, 0) * Rot(0, p["ring_tilt"], 0) * ring).fuse(
        Pos(-half, 0, 0) * Rot(0, -p["ring_tilt"], 0) * ring,
        _web(p, half),
        tol=1e-3,
    )

    # ---- เจาะรูวงแหวนซ้ำ: เฉือนแผ่นคานส่วนที่พาดผ่านรู ให้รูสวมสะอาดพอดีขนาด ----
    bore_cut = Cylinder(_bore_dia(p) / 2, p["ring_w"] + p["beam_t"] + 4)
    part -= Pos(half, 0, 0) * Rot(0, p["ring_tilt"], 0) * bore_cut
    part -= Pos(-half, 0, 0) * Rot(0, -p["ring_tilt"], 0) * bore_cut

    # ---- รูกลมลดน้ำหนัก ----
    n = int(p["holes_n"])
    for i in range(n):
        x = p["holes_x"] + (i - (n - 1) / 2) * p["holes_pitch"]
        part -= Pos(x, 0, 0) * Cylinder(p["holes_dia"] / 2, p["beam_t"] + 2)

    # ---- ช่อง slot ยาว ----
    if p["slot_l"] > 0:
        sk = Plane.XY.offset(-p["beam_t"]) * Pos(p["slot_x"], 0, 0) * SlotOverall(
            p["slot_l"], p["slot_w"])
        part -= extrude(sk, 2 * p["beam_t"])

    return part


if __name__ == "__main__":
    from partkit.cli import run_cli
    run_cli(build, PARAMS, "dual_ring_bar")
