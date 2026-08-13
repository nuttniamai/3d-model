"""โครงในลำโพง JBL Flip 4 — ปลอกคู่ยึด passive radiator สองข้าง เชื่อมด้วยแผ่นฐาน
(จำลองจากไฟล์ต้นฉบับที่วัดขนาดด้วย trimesh)

อะไหล่แท้: รหัส 55-FLP4H1-0UHB1 "Rubber front casing JBL Flip 4"
วัสดุเดิม PC+TPU (โครง PC แข็ง หุ้มยาง TPU) — งานปริ้นทดแทนแนะนำ PETG
หมายเหตุ: Flip 4 มีสองรุ่นย่อย (ก่อน/หลังปี 2017, radiator ยึดต่างกัน
และใช้แทนกันไม่ได้) — วัดเครื่องของตัวเองก่อนปริ้นเสมอ

โครงสร้าง (แกน X = แนวยาวของชิ้น):
- ปลอกทรงกระบอก 2 ข้าง แกนรูชี้ตามแนว X (สวมท่อ/แกนได้ทะลุ)
- แผ่นเชื่อมแบนหนา plate_t วางชิดขอบล่างของวง (ระนาบ XZ, ความหนาตามแกน Y)
- โคนบาน (bell) เชื่อมแผ่นเข้ากับปลอกทั้งสองข้าง
- แผ่นเจาะ: รูกลม + สลอตยาว + สลอตตั้งทะลุโคนซ้าย

ค่า default ทุกตัววัดจากไฟล์ STL ต้นฉบับ — แก้เฉพาะจุดที่ต้องการได้เลย:
    python parts/dual_ring_bar.py                 # ตามต้นฉบับ
    python parts/dual_ring_bar.py --ring-bore 54  # เช่นวัดท่อจริงได้ 54

การปริ้น: หมุนใน Bambu Studio ให้แผ่นราบลงเตียง แล้วเปิด support
สำหรับส่วนโค้งของปลอกวงแหวน (tree support แนะนำ)
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build123d import (Align, Box, Cone, Cylinder, Plane, Pos, Rot,
                       SlotOverall, extrude)
from partkit import fdm

# ---- พารามิเตอร์ (mm) — วัดจากไฟล์ต้นฉบับ ----
PARAMS = dict(
    length=170.3,      # ความยาวรวมทั้งชิ้น
    ring_od=60.0,      # เส้นผ่านศูนย์กลางนอกปลอก
    ring_bore=55.0,    # รูในปลอก (ตามไฟล์เดิมเป๊ะ — ดู fit ด้านล่าง)
    ring_w=13.3,       # ความกว้างปลอกตามแนวแกน
    neck_len=9.2,      # ความยาวโคนบานจากปลอกเข้าหาแผ่น
    fit="none",        # "none" = ใช้ ring_bore ตรง ๆ ตามไฟล์เดิม
                       # press/tight/slide/loose = ตีความ ring_bore เป็นขนาด
                       # "ท่อจริงที่จะสวม" แล้วเผื่อค่าหด FDM ให้อัตโนมัติ
    plate_t=5.7,       # ความหนาแผ่นเชื่อม
    plate_h=30.4,      # ความสูงแผ่น (แกน Z)
    plate_drop=0.8,    # แผ่นยื่นต่ำกว่าขอบล่างของวงเท่าไร
    gusset_rise=6.5,   # ขอบบนโคนบานไต่สูงขึ้นจากผิวในแผ่นเมื่อเข้าใกล้วง
    holes_n=3,         # รูกลมลดน้ำหนัก (0 = ไม่เจาะ)
    holes_dia=10.5,
    holes_pitch=14.75,
    holes_x=-22.0,     # ศูนย์กลางกลุ่มรู (ลบ = ฝั่งซ้าย)
    holes_z=-1.0,
    slot_l=44.0,       # สลอตยาวฝั่งขวา (0 = ไม่เจาะ)
    slot_w=13.5,
    slot_x=34.2,
    slot_z=-0.3,
    vslot_n=2,         # สลอตแนวตั้งทะลุโคนวงซ้าย (0 = ไม่เจาะ)
    vslot_w=6.0,
    vslot_h=13.5,
    vslot_x=-65.2,     # ศูนย์กลางสลอตตั้งช่องแรก
    vslot_pitch=8.5,   # ระยะห่างช่องถัดไป (ไปทางขวา)
    vslot_z=-0.5,
)

FITS = dict(press=fdm.FIT_PRESS, tight=fdm.FIT_TIGHT,
            slide=fdm.FIT_SLIDE, loose=fdm.FIT_LOOSE)


def _bore_dia(p):
    f = str(p["fit"]).lower()
    if f in ("none", ""):
        return p["ring_bore"]
    return fdm.hole_dia(p["ring_bore"], FITS[f])


def _y_cutter(profile_2d, y_span=200):
    """เปลี่ยน sketch บนระนาบ XZ เป็นแท่งเจาะทะลุตามแกน Y"""
    sk = Plane.XZ.offset(-y_span / 2) * profile_2d
    return extrude(sk, y_span)


def build(p):
    bore = _bore_dia(p)
    wall = (p["ring_od"] - bore) / 2
    if wall < fdm.MIN_WALL:
        raise ValueError(
            f"ผนังปลอกบางเกินไป: ring_od ต้อง >= {bore + 2 * fdm.MIN_WALL:.1f} mm")

    x_out = p["length"] / 2                      # ปลายนอกปลอก
    x_in = x_out - p["ring_w"]                   # ปลายในปลอก (เริ่มโคน)
    x_cone = x_in - p["neck_len"]                # โคนจบ ชนแผ่น
    if x_cone <= 10:
        raise ValueError("length สั้นเกินไปเมื่อเทียบกับ ring_w + neck_len")

    plate_bot = -p["ring_od"] / 2 - p["plate_drop"]   # ผิวนอกแผ่น (y ต่ำสุด)
    plate_top = plate_bot + p["plate_t"]              # ผิวในแผ่น

    # ---- ปลอกวงแหวน 2 ข้าง (แกน X) ----
    sleeve = Rot(0, 90, 0) * (Cylinder(p["ring_od"] / 2, p["ring_w"])
                              - Cylinder(bore / 2, p["ring_w"] + 2))
    ring_cx = x_in + p["ring_w"] / 2

    # ---- แผ่นเชื่อม (ยื่นเข้าเขตโคน/ปลอกเล็กน้อยให้เชื่อมสนิท แล้วคว้านรูซ้ำ) ----
    plate = Pos(0, plate_bot + p["plate_t"] / 2, 0) * Box(
        2 * (x_in + 2), p["plate_t"], p["plate_h"])

    # ---- โคนบาน: เปลือกกรวยรอบแกน X ตัดเหลือซีกล่างด้วยระนาบเอียง ----
    def bell(side):
        h = p["neck_len"] + 1.5                 # จมเข้าปลอก 1.5 mm
        r_small = p["plate_h"] / 2
        outer = Cone(r_small, p["ring_od"] / 2, h)
        inner = Cone(max(r_small - wall, 2), p["ring_od"] / 2 - wall, h + 2)
        shell = outer - inner
        # Cone โตจากปลายเล็ก (-Z) ไปปลายใหญ่ (+Z); Rot(0, 90*side, 0)
        # หันปลายใหญ่ไปทางปลอกของฝั่งนั้น แล้วเลื่อนให้ปลายเล็กอยู่ที่ x_cone
        shell = Pos(side * (x_cone + h / 2), 0, 0) * Rot(0, 90 * side, 0) * shell
        # ระนาบตัดเอียง: ผ่าน (x_cone, plate_top) ไต่ขึ้น gusset_rise เมื่อถึงปลอก
        ang = math.degrees(math.atan2(p["gusset_rise"], p["neck_len"]))
        keep = Pos(side * x_cone, plate_top, 0) * Rot(0, 0, side * ang) * Box(
            1000, 1000, 1000, align=(Align.CENTER, Align.MAX, Align.CENTER))
        return shell & keep

    part = (Pos(ring_cx, 0, 0) * sleeve).fuse(
        Pos(-ring_cx, 0, 0) * sleeve,
        plate,
        bell(+1),
        bell(-1),
        tol=1e-3,
    )

    # ---- คว้านรูปลอกซ้ำให้สะอาด (เฉือนแผ่น/โคนที่ล้ำเข้ารู) ----
    cut_len = p["ring_w"] + p["neck_len"] + 2
    bore_cut = Rot(0, 90, 0) * Cylinder(bore / 2, cut_len)
    for s in (1, -1):
        part -= Pos(s * (x_out + 1 - cut_len / 2), 0, 0) * bore_cut

    # ---- รูกลม ----
    n = int(p["holes_n"])
    for i in range(n):
        x = p["holes_x"] + (i - (n - 1) / 2) * p["holes_pitch"]
        part -= Pos(x, 0, p["holes_z"]) * Rot(90, 0, 0) * Cylinder(
            p["holes_dia"] / 2, 200)

    # ---- สลอตยาวแนวนอน ----
    if p["slot_l"] > 0:
        part -= Pos(p["slot_x"], 0, p["slot_z"]) * _y_cutter(
            SlotOverall(p["slot_l"], p["slot_w"]))

    # ---- สลอตแนวตั้งทะลุโคน/ปลอกซ้าย ----
    for i in range(int(p["vslot_n"])):
        x = p["vslot_x"] + i * p["vslot_pitch"]
        part -= Pos(x, 0, p["vslot_z"]) * _y_cutter(
            Rot(0, 0, 90) * SlotOverall(p["vslot_h"], p["vslot_w"]))

    return part


if __name__ == "__main__":
    from partkit.cli import run_cli
    run_cli(build, PARAMS, "dual_ring_bar")
