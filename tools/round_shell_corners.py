"""ลบมุมทั้ง 4 ของเปลือกทรงกระบอกรูปตัว C ให้เป็นส่วนโค้งรัศมีที่กำหนด

ใช้กับชิ้นงานที่เป็นเปลือกทรงกระบอกผ่าเปิด (แกน Z) ขอบบน/ล่างเป็นระนาบ
(จะเอียงหรือไม่ก็ได้) — มุมทั้ง 4 คือจุดที่หน้าตัดปลายเปิดชนขอบบน/ล่าง

    python tools/round_shell_corners.py case1.stl -r 21.5 -o case1_rounded.stl
    python tools/round_shell_corners.py case1.stl --ref d_case1.stl -o out.stl

วิธีตัด — ส่วนโค้งบน "ผิวที่คลี่ออก":
วัดระยะตามผิวโค้ง (arc length) จากหน้าตัดปลายเปิด แล้ววางส่วนโค้งรัศมี R
ให้สัมผัสพอดีทั้งหน้าตัดและเส้นขอบ ได้รอยต่อเรียบไม่มีสะดุดทั้งสองด้าน
(ทรงกระบอกที่แกนชี้ตามแนวรัศมีสัมผัสระนาบขอบ "เอียง" ไม่ได้จริง เพราะแกน
 ไม่ขนานกับระนาบนั้น — จึงใช้การคลี่ผิวแทน ได้รัศมีตามที่สั่งเป๊ะ)

ชิ้นงานสมมาตรทั้งแกน y และ z จึงสร้างก้อนตัดมุมเดียวแล้วสะท้อนเอาอีก 3 มุม
ส่วนอื่นของชิ้นงานไม่ถูกแตะเลย
"""
import argparse

import numpy as np
import trimesh

N_SEG = 90           # ความละเอียดของส่วนโค้ง (1 องศาต่อช่วง)


def ref_radius(path):
    v = trimesh.load(path).vertices
    c = v.mean(axis=0)
    n = np.linalg.svd(v - c)[2][2]
    return float(np.linalg.norm((v - c) - np.outer((v - c) @ n, n), axis=1).mean())


def measure(mesh):
    """มุมหน้าตัดปลายเปิดฝั่ง +y, รัศมีนอก, ระนาบขอบบน"""
    v = mesh.vertices
    ang = np.degrees(np.arctan2(v[:, 1], v[:, 0]))
    a_sorted = np.sort(ang)
    theta = float(a_sorted[np.diff(a_sorted).argmax() + 1])
    r_out = float(np.hypot(v[:, 0], v[:, 1]).max())
    top = v[v[:, 2] > v[:, 2].max() * 0.8]
    top = top[np.hypot(top[:, 0], top[:, 1]) > r_out - 0.2]
    cx, cy, c0 = np.linalg.lstsq(np.c_[top[:, 0], top[:, 1], np.ones(len(top))],
                                 top[:, 2], rcond=None)[0]
    return theta, r_out, (float(cx), float(cy), float(c0))


def corner_tool(theta_deg, r_out, plane, R):
    """ก้อนตัดของมุม 'บน ฝั่ง +y' — สร้าง mesh ตรง ๆ เป็นลิ่มเชิงมุมที่ก้นเป็นส่วนโค้ง"""
    cx, cy, c0 = plane
    th0 = np.radians(theta_deg)

    def z_rim(s):
        """ระดับขอบบน ณ ระยะตามผิว s จากหน้าตัด"""
        a = th0 + s / r_out
        return cx * r_out * np.cos(a) + cy * r_out * np.sin(a) + c0

    # ศูนย์กลางส่วนโค้ง: s = R (สัมผัสหน้าตัด), z หาให้ห่างเส้นขอบ = R พอดี
    s_c = R
    lo, hi = z_rim(s_c) - 2 * R, z_rim(s_c)
    for _ in range(80):                       # ไล่หาแบบแบ่งครึ่ง
        z_c = (lo + hi) / 2
        ss = np.linspace(0, 3 * R, 4000)
        d = np.hypot(ss - s_c, z_rim(ss) - z_c).min()
        if d > R:          # ศูนย์กลางต่ำไป ห่างขอบเกิน R -> ยกขึ้น
            lo = z_c
        else:              # ใกล้ขอบเกินไป -> กดลง
            hi = z_c
    z_c = (lo + hi) / 2
    print(f"    ศูนย์กลางส่วนโค้ง: s={s_c:.3f} z={z_c:.3f}"
          f"   ปลายส่วนโค้งที่ s={s_c:.2f} (มุมกว้าง {np.degrees(s_c/r_out):.2f}°)")

    # ก้นลิ่ม = ส่วนโค้ง สุ่มจุดตาม "มุมของส่วนโค้ง" (ไม่ใช่ตาม s) เพื่อให้
    # ช่วงต้นโค้งที่เกือบตั้งฉากละเอียดพอ ๆ กับช่วงปลาย
    phi = np.linspace(np.pi, np.pi / 2, N_SEG + 1)
    s = s_c + R * np.cos(phi)
    zb = z_c + R * np.sin(phi)
    ang = th0 + s / r_out
    z_top = 200.0
    r_in, r_o = 20.0, r_out + 5.0             # คลุมความหนาผนัง (32..33.5) สบาย ๆ

    V, F = [], []
    for j in range(N_SEG + 1):
        ca, sa = np.cos(ang[j]), np.sin(ang[j])
        V += [[r_in * ca, r_in * sa, zb[j]], [r_o * ca, r_o * sa, zb[j]],
              [r_in * ca, r_in * sa, z_top], [r_o * ca, r_o * sa, z_top]]
    V = np.array(V)

    def quad(a, b, c, d):
        F.append([a, b, c]); F.append([a, c, d])

    for j in range(N_SEG):
        k, n = 4 * j, 4 * (j + 1)
        quad(k + 0, k + 1, n + 1, n + 0)      # ก้น (ส่วนโค้ง)
        quad(k + 2, k + 3, n + 3, n + 2)      # ฝาบน
        quad(k + 1, k + 3, n + 3, n + 1)      # ผิวนอก
        quad(k + 0, k + 2, n + 2, n + 0)      # ผิวใน
    e = 4 * N_SEG
    quad(0, 1, 3, 2)                          # ฝาปิดหัว (ที่หน้าตัดปลายเปิด)
    quad(e + 0, e + 1, e + 3, e + 2)          # ฝาปิดท้าย
    m = trimesh.Trimesh(vertices=V, faces=np.array(F), process=True)
    m.fix_normals()
    return m


def mirrored(mesh, sy=1, sz=1):
    m = mesh.copy()
    m.apply_transform(np.diag([1.0, sy, sz, 1.0]))
    m.fix_normals()
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", help="STL ของเปลือกตัว C ที่จะลบมุม")
    ap.add_argument("-o", "--out", required=True, help="ไฟล์ผลลัพธ์")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("-r", "--radius", type=float, help="รัศมีส่วนโค้ง (mm)")
    g.add_argument("--ref", help="STL แผ่นกลมอ้างอิง ใช้รัศมีของแผ่นนั้น")
    args = ap.parse_args()

    case = trimesh.load(args.src)
    R = args.radius if args.radius else ref_radius(args.ref)
    theta, r_out, plane = measure(case)
    print(f"รัศมีที่ใช้ = {R:.4f} mm")
    print(f"หน้าตัดปลายเปิด ±{abs(theta):.3f}°   รัศมีนอก {r_out:.3f}")
    print(f"ระนาบขอบบน: z = {plane[0]:+.5f}x {plane[1]:+.5f}y {plane[2]:+.3f}")

    base = corner_tool(theta, r_out, plane, R)
    print(f"    ก้อนตัด watertight={base.is_watertight} vol={base.volume/1000:.2f} cm3")

    tools = trimesh.boolean.union([base, mirrored(base, sy=-1),
                                   mirrored(base, sz=-1),
                                   mirrored(base, sy=-1, sz=-1)])
    out = case.difference(tools)          # ตัดครั้งเดียว ลดโอกาสเกิดรอยต่อเสีย
    out.merge_vertices()
    out.update_faces(out.nondegenerate_faces())
    out.fix_normals()

    print(f"\nผลลัพธ์: watertight={out.is_watertight}  faces={len(out.faces)}")
    print(f"  ปริมาตร {case.volume/1000:.2f} -> {out.volume/1000:.2f} cm3"
          f"   (ตัดออก {(case.volume-out.volume)/1000:.2f} cm3)")
    print(f"  bounds {np.round(out.bounds[0],2)} .. {np.round(out.bounds[1],2)}")
    out.export(args.out)
    print(f"  -> {args.out}")


if __name__ == "__main__":
    main()
