"""Export ชิ้นงานเป็น STL / 3MF / STEP พร้อมตรวจสุขภาพ mesh ก่อนปริ้น"""
import os

from build123d import Mesher, export_step, export_stl


def export_part(part, name: str, out_dir: str = "out", formats=("stl", "3mf", "step"),
                check: bool = True, verbose: bool = True) -> dict:
    """Export ชิ้นงานลง out_dir คืน dict {format: path}

    - STL/3MF: หน่วย mm พร้อมลากเข้า Bambu Studio ทันที
    - STEP:    สำหรับเปิดแก้ต่อใน FreeCAD หรือส่งให้คนอื่น (เก็บผิวโค้งจริง)
    - check=True: โหลด STL กลับมาตรวจว่า mesh ปิดสนิท (watertight) ก่อนเอาไปปริ้น
    """
    os.makedirs(out_dir, exist_ok=True)
    paths = {}

    if "stl" in formats:
        p = os.path.join(out_dir, f"{name}.stl")
        export_stl(part, p)
        paths["stl"] = p
    if "3mf" in formats:
        p = os.path.join(out_dir, f"{name}.3mf")
        m = Mesher()
        m.add_shape(part)
        m.write(p)
        paths["3mf"] = p
    if "step" in formats:
        p = os.path.join(out_dir, f"{name}.step")
        export_step(part, p)
        paths["step"] = p

    bb = part.bounding_box()
    size = (bb.size.X, bb.size.Y, bb.size.Z)

    if check and "stl" in paths:
        import trimesh

        mesh = trimesh.load(paths["stl"])
        if not mesh.is_watertight:
            raise RuntimeError(
                f"[{name}] mesh ไม่ปิดสนิท (not watertight) — อย่าเพิ่งปริ้น "
                f"ลองเช็ค boolean ที่ผิวชนกันพอดี แล้ว generate ใหม่"
            )

    if verbose:
        print(f"[{name}] ขนาดจริง {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} mm")
        for fmt, p in paths.items():
            print(f"  -> {p}")

    return paths
