"""เจาะร่องในบล็อกเคส ให้ชิ้นงานสไลด์ทะลุตามแกนที่กำหนดได้ตลอด

หลักการ: ถ้าชิ้นงานต้องเลื่อนทะลุออกไปทั้งสองด้านตามแกนหนึ่ง ปริมาตรที่มัน
กวาดผ่านคือ "เงาของชิ้นงานบนระนาบตั้งฉากกับแกนนั้น" ยืดออกไปตลอดความยาว
จึงหาเงา 2 มิติแล้ว extrude ทะลุบล็อก ไม่ต้องไล่ union ทีละตำแหน่ง

    python tools/slide_channel.py block.stl --tool part.stl -o out.stl
    python tools/slide_channel.py block.stl --tool part.stl -o out.stl --clearance 0.25
"""
import argparse

import numpy as np
import trimesh
from trimesh.geometry import plane_transform
from trimesh.path import polygons

AXES = {"x": [1.0, 0, 0], "y": [0, 1.0, 0], "z": [0, 0, 1.0]}


def channel(part, axis, length, clearance=0.0, origin=None):
    """ก้อนเจาะ = เงาของ part ตั้งฉากกับ axis ยืดยาว length"""
    n = np.array(AXES[axis])
    org = np.zeros(3) if origin is None else np.asarray(origin, float)
    poly = polygons.projected(part, normal=n, origin=org)
    if poly is None:
        raise RuntimeError("หาเงาของชิ้นงานไม่ได้")
    if clearance:
        poly = poly.buffer(clearance, join_style=2)
    # เงาที่ได้มักมีจุดซ้ำ/จุดเรียงตรงกัน ทำให้ triangulation ออกมาไม่ปิดสนิท
    # ตัดทิ้งด้วย tolerance ระดับไมครอน (ไม่กระทบขนาดจริง)
    poly = poly.simplify(1e-6)
    solid = trimesh.creation.extrude_polygon(poly, height=length)
    if not solid.is_volume:
        raise RuntimeError("ก้อนเจาะไม่ปิดสนิท")
    T = plane_transform(org, n)
    solid.apply_transform(np.linalg.inv(T))
    return solid.apply_translation(-n * length / 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("block", help="STL ของบล็อกที่จะเจาะ")
    ap.add_argument("--tool", required=True, help="STL ของชิ้นงานที่ต้องสไลด์ผ่าน")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--axis", default="y", choices=list(AXES), help="แกนที่สไลด์ (default y)")
    ap.add_argument("--clearance", type=float, default=0.0,
                    help="ระยะเผื่อรอบด้าน (mm) 0 = พอดีเป๊ะ")
    args = ap.parse_args()

    block = trimesh.load(args.block)
    part = trimesh.load(args.tool)
    i = "xyz".index(args.axis)
    length = (block.bounds[1][i] - block.bounds[0][i]) + 20.0   # ยาวเกินบล็อกให้ทะลุแน่

    cut = channel(part, args.axis, length, args.clearance)
    print(f"บล็อก : {np.round(block.extents,2)}  ปริมาตร {block.volume/1000:.2f} cm3")
    print(f"ชิ้นงาน: {np.round(part.extents,2)}")
    print(f"ก้อนเจาะ: ยาว {length:.1f} mm ตามแกน {args.axis}  เผื่อ {args.clearance} mm"
          f"  watertight={cut.is_watertight}")

    out = block.difference(cut)
    out.merge_vertices()
    out.update_faces(out.nondegenerate_faces())
    out.fix_normals()
    print(f"\nผลลัพธ์: watertight={out.is_watertight}  faces={len(out.faces)}")
    print(f"  ปริมาตร {block.volume/1000:.2f} -> {out.volume/1000:.2f} cm3"
          f"   (เจาะออก {(block.volume-out.volume)/1000:.2f} cm3)")

    # ตรวจการสไลด์: วัด "ความลึกที่จมเข้าเนื้อ" ไม่ใช่ contains เพราะที่ clearance=0
    # ผิวชิ้นงานแนบผิวร่องพอดี จุดบนผิวจะตัดสิน in/out ไม่ได้
    worst = -1e9
    for t in np.linspace(block.bounds[0][i] - part.extents[i],
                         block.bounds[1][i] + part.extents[i], 15):
        p = part.copy()
        p.apply_translation(np.array(AXES[args.axis]) * (t - part.centroid[i]))
        worst = max(worst, float(trimesh.proximity.signed_distance(out, p.vertices).max()))
    print(f"  ตรวจการสไลด์ 15 ตำแหน่ง: จมเข้าเนื้อบล็อกลึกสุด {max(worst,0):.4f} mm")

    out.export(args.out)
    print(f"  -> {args.out}")


if __name__ == "__main__":
    main()
