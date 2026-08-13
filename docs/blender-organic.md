# ใช้ PartKit คู่กับ Blender

แนวคิด: **งานเรขาคณิต/วัดขนาด → PartKit, งานปั้นอิสระ/โค้ง organic → Blender**
สองอย่างนี้เสริมกัน ไม่ต้องเลือกอย่างเดียว

## เอาชิ้นงาน PartKit เข้า Blender

1. Blender ตั้งหน่วยก่อน (ครั้งเดียวต่อไฟล์): Scene Properties → Units →
   Unit System = Metric, **Unit Scale = 0.001, Length = Millimeters**
   (ค่า default ของ Blender คือเมตร ถ้าไม่ตั้งจะสับสนเวลา export ไปปริ้น)
2. File → Import → **STL** เลือกไฟล์จาก `out/`
   - Blender 4.x มี importer STEP ไม่ได้ในตัว ถ้าอยากได้ผิวโค้งจริงให้เปิด
     `.step` ใน FreeCAD (ฟรี) แล้ว export เป็น STL ความละเอียดสูงแทน
3. แต่งต่อได้ตามถนัด: sculpt, bevel, boolean กับรูปทรงอิสระ
4. Export กลับ: File → Export → STL แล้วเช็คว่า scale = 1.0

## Add-on ฟรีที่แนะนำสำหรับงานปริ้น

| Add-on | ใช้ทำอะไร | ราคา |
|---|---|---|
| **3D Print Toolbox** (มากับ Blender อยู่แล้ว ไปเปิดใน Preferences → Add-ons) | เช็ค manifold/ผนังบาง/ยื่นเกิน ก่อนปริ้น | ฟรี |
| [CAD Sketcher](https://github.com/hlorus/CAD_Sketcher) | สเก็ตช์ 2D แบบใส่ dimension/constraint เหมือน CAD ใน Blender | ฟรี |
| [MeasureIt](https://docs.blender.org/manual/en/latest/addons/3d_view/measureit.html) (มากับ Blender) | โชว์เส้นบอกขนาดจริงบนโมเดล | ฟรี |

## ข้อควรระวังเวลาปั้นใน Blender สำหรับงาน true-to-scale

- ก่อน export กด `Ctrl+A → All Transforms` เสมอ (apply scale)
  ไม่งั้นขนาดใน Bambu Studio จะเพี้ยนจากตัวเลขที่เห็น
- Blender ไม่มีระบบ "ค่าเผื่อรู FDM" — ถ้าเจาะรูสวมแกนใน Blender
  ให้บวกเส้นผ่านศูนย์กลางเพิ่มเองตามตาราง `partkit/fdm.py`
  (ง่ายกว่านั้น: ทำส่วนที่ต้องแม่นใน PartKit แล้วค่อยเอาไปแต่งใน Blender)
- ใช้ 3D Print Toolbox กด Check All ก่อน export ทุกครั้ง
