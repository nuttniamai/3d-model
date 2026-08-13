# PartKit — สร้างชิ้นส่วน 3D แบบ true-to-scale สำหรับ Bambu Lab P2S

เครื่องมือ Python สำหรับ "ปั้นชิ้นส่วนใช้งานจริง" ที่ไม่มีใครทำโมเดลไว้ให้ —
ขายึด แหวนรอง ตะขอ กล่อง ลูกบิด ฯลฯ โดย **ระบุขนาดเป็นมิลลิเมตรตรง ๆ**
แก้ตัวเลขแล้วรันใหม่ได้ทันที ไม่ต้องปั้นมือใน Blender

ฟรีและโอเพนซอร์สทั้งหมด ใช้ [build123d](https://github.com/gumyr/build123d)
(kernel CAD ตัวเดียวกับ FreeCAD) จึงแม่นยำระดับงานวิศวกรรมจริง

## ติดตั้ง (ครั้งเดียว)

ต้องมี Python 3.10 ขึ้นไป แล้วรัน:

```bash
pip install -r requirements.txt
```

## ใช้งาน

แต่ละไฟล์ใน `parts/` คือแม่แบบชิ้นส่วน 1 ชนิด รันได้ทันที:

```bash
python parts/spacer.py                          # ใช้ขนาด default
python parts/spacer.py --inner-dia 8.2 --outer-dia 16 --height 5
python parts/bracket_L.py --leg-a 60 --thickness 5 --screw M5
python parts/box_with_lid.py --inner-l 80 --inner-w 50 --inner-d 30
python parts/knob.py --shaft d --shaft-dia 6 --flat-depth 1.5
python parts/wall_hook.py --arm-len 40
python parts/dual_ring_bar.py --ring-bore 54 --fit slide
```

ไฟล์ผลลัพธ์อยู่ในโฟลเดอร์ `out/` — ได้ 3 ฟอร์แมตต่อชิ้น:

| ไฟล์ | เอาไปทำอะไร |
|---|---|
| `.3mf` / `.stl` | ลากเข้า **Bambu Studio** แล้วปริ้นได้เลย (หน่วย mm) |
| `.step` | เปิดแก้ต่อใน FreeCAD หรือส่งให้โรงกลึง (เก็บผิวโค้งจริง ไม่ใช่ mesh) |

ดูพารามิเตอร์ทั้งหมดของแต่ละชิ้น: `python parts/<ชื่อ>.py --help`
(หรือเปิดไฟล์ดูบล็อก `PARAMS` หัวไฟล์ — มีคำอธิบายภาษาไทยทุกตัว)

## แม่แบบที่มีให้

| ไฟล์ | ชิ้นส่วน |
|---|---|
| `parts/bracket_L.py` | ขายึดฉากตัว L พร้อมรูสกรูหัวจม + มุมโค้งรับแรง |
| `parts/spacer.py` | แหวนรอง/บูช เลือกความแน่นการสวมได้ 4 ระดับ |
| `parts/wall_hook.py` | ตะขอแขวนผนังตัว J พร้อมรูสกรู |
| `parts/box_with_lid.py` | กล่อง+ฝาสวม ระบุขนาด "ภายใน" แล้วคิดค่าเผื่อฝาให้เอง |
| `parts/knob.py` | ลูกบิดสวมแกนกลม / แกนปาด D / หกเหลี่ยม |
| `parts/dual_ring_bar.py` | โครงในลำโพง JBL Flip 4 (ปลอกยึด passive radiator คู่ + แผ่นฐาน) |

## จุดเด่นเรื่อง true-to-scale

- ทุกหน่วยเป็น **mm ตรงกับของจริง** ไม่มีการ scale ทีหลัง
- `partkit/fdm.py` มี**ค่าเผื่อการพิมพ์ FDM ในตัว**: รูแนวตั้งบนเครื่อง FDM
  จะพิมพ์เล็กกว่าแบบเสมอ (~0.2 mm) โปรแกรมชดเชยให้อัตโนมัติ
  และมี preset ความแน่นการสวม 4 ระดับ (`press / tight / slide / loose`)
- `partkit/fasteners.py` มีตารางสกรูเมตริก **M2–M8** ครบ:
  รูสวม รูเกลียวปล่อย ช่องหัวจม หัวเตเปอร์ ช่องน็อตหกเหลี่ยม ช่อง heat-set insert
- ก่อน export ทุกครั้งจะ**ตรวจ mesh ว่าปิดสนิท (watertight)** ให้อัตโนมัติ
  ถ้าโมเดลรั่วจะเตือนก่อนเสียเวลา+เส้นพลาสติกไปปริ้น

## สร้างชิ้นส่วนแบบใหม่ของตัวเอง

ก๊อปปี้ไฟล์ใน `parts/` ที่ใกล้เคียงที่สุดมาแก้ ตัวอย่างชิ้นง่ายสุด:

```python
from build123d import Box, Pos
from partkit import clearance_hole

PARAMS = dict(width=30.0, depth=20.0, thickness=4.0)

def build(p):
    part = Box(p["width"], p["depth"], p["thickness"])
    part -= Pos(0, 0, p["thickness"] / 2) * clearance_hole("M4", p["thickness"] + 1)
    return part

if __name__ == "__main__":
    from partkit.cli import run_cli
    run_cli(build, PARAMS, "my_part")
```

อยากเห็นโมเดลสด ๆ ระหว่างแก้โค้ด ติดตั้งส่วนขยาย
[OCP CAD Viewer](https://github.com/bernhard-42/vscode-ocp-cad-viewer) ใน VS Code (ฟรี)

## เอกสารเพิ่มเติม

- [docs/workflow-bambu.md](docs/workflow-bambu.md) — ขั้นตอนวัดของจริง → generate → ปริ้นกับ Bambu Studio + เคล็ดลับจูนค่าเผื่อ
- [docs/blender-organic.md](docs/blender-organic.md) — เอาชิ้นงานไปแต่งต่อใน Blender + add-on ฟรีที่ควรมี

## ทดสอบ

```bash
python -m pytest
```

ตรวจว่าทุกแม่แบบสร้าง solid ได้, ขนาด bounding box ตรงพารามิเตอร์ (ยืนยัน
true-to-scale), และ mesh ปิดสนิทพร้อมปริ้น
