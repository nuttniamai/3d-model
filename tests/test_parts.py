"""ตรวจว่าแม่แบบทุกชิ้น: สร้างได้, ขนาดตรงพารามิเตอร์ (true-to-scale),
และ mesh ปิดสนิทพร้อมปริ้น
"""
import importlib.util
import math
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build123d import GeomType  # noqa: E402
from partkit import fdm  # noqa: E402
from partkit.export import export_part  # noqa: E402

TOL = 0.01  # mm — ความคลาดเคลื่อนเชิงตัวเลขของ kernel


def load_part(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "parts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def bbox(part):
    bb = part.bounding_box()
    return bb.size.X, bb.size.Y, bb.size.Z


def assert_watertight(part, name, tmp_path):
    import trimesh

    export_part(part, name, out_dir=str(tmp_path), formats=("stl",),
                check=False, verbose=False)
    mesh = trimesh.load(tmp_path / f"{name}.stl")
    assert mesh.is_watertight, f"{name}: mesh ไม่ปิดสนิท"


def test_bracket_L(tmp_path):
    mod = load_part("bracket_L")
    p = dict(mod.PARAMS)
    part = mod.build(p)
    x, y, z = bbox(part)
    assert math.isclose(x, p["leg_a"], abs_tol=TOL)
    assert math.isclose(y, p["width"], abs_tol=TOL)
    assert math.isclose(z, p["leg_b"], abs_tol=TOL)
    assert_watertight(part, "bracket_L", tmp_path)


def test_bracket_L_custom_params(tmp_path):
    mod = load_part("bracket_L")
    p = dict(mod.PARAMS, leg_a=70.0, leg_b=40.0, thickness=5.0, screw="M5")
    part = mod.build(p)
    x, y, z = bbox(part)
    assert math.isclose(x, 70.0, abs_tol=TOL)
    assert math.isclose(z, 40.0, abs_tol=TOL)
    assert_watertight(part, "bracket_L_custom", tmp_path)


def test_spacer(tmp_path):
    mod = load_part("spacer")
    p = dict(mod.PARAMS)
    part = mod.build(p)
    x, y, z = bbox(part)
    assert math.isclose(x, p["outer_dia"], abs_tol=TOL)
    assert math.isclose(z, p["height"], abs_tol=TOL)
    # ปริมาตรต้องน้อยกว่าทรงกระบอกตัน = มีรูจริง
    solid_vol = math.pi * (p["outer_dia"] / 2) ** 2 * p["height"]
    assert part.volume < solid_vol * 0.85
    assert_watertight(part, "spacer", tmp_path)


def test_spacer_wall_too_thin():
    mod = load_part("spacer")
    p = dict(mod.PARAMS, inner_dia=14.0, outer_dia=15.0)
    with pytest.raises(ValueError):
        mod.build(p)


def test_wall_hook(tmp_path):
    mod = load_part("wall_hook")
    p = dict(mod.PARAMS)
    part = mod.build(p)
    x, y, z = bbox(part)
    assert math.isclose(x, p["plate_t"] + p["arm_len"], abs_tol=TOL)
    assert math.isclose(y, p["plate_w"], abs_tol=TOL)
    assert math.isclose(z, p["plate_h"], abs_tol=TOL)
    assert_watertight(part, "wall_hook", tmp_path)


def test_box_with_lid(tmp_path):
    mod = load_part("box_with_lid")
    p = dict(mod.PARAMS)
    parts = mod.build(p)
    bx, by, bz = bbox(parts["box"])
    assert math.isclose(bx, p["inner_l"] + 2 * p["wall"], abs_tol=TOL)
    assert math.isclose(by, p["inner_w"] + 2 * p["wall"], abs_tol=TOL)
    assert math.isclose(bz, p["inner_d"] + p["bottom_t"], abs_tol=TOL)
    lx, ly, lz = bbox(parts["lid"])
    # ขอบฝาต้องเล็กกว่าช่องภายในกล่อง = สวมได้จริง
    assert lx <= bx + TOL and ly <= by + TOL
    assert math.isclose(lz, p["lid_t"] + p["lip_h"], abs_tol=TOL)
    assert_watertight(parts["box"], "box", tmp_path)
    assert_watertight(parts["lid"], "lid", tmp_path)


@pytest.mark.parametrize("shaft", ["round", "d", "hex"])
def test_knob_shafts(tmp_path, shaft):
    mod = load_part("knob")
    p = dict(mod.PARAMS, shaft=shaft)
    part = mod.build(p)
    x, y, z = bbox(part)
    assert x <= p["dia"] + TOL and y <= p["dia"] + TOL
    assert math.isclose(z, p["height"], abs_tol=TOL)
    assert_watertight(part, f"knob_{shaft}", tmp_path)


def test_dual_ring_bar(tmp_path):
    mod = load_part("dual_ring_bar")
    p = dict(mod.PARAMS)
    part = mod.build(p)
    x, y, z = bbox(part)
    assert math.isclose(x, p["length"], abs_tol=TOL)
    # รัศมีสูงสุดมาจากเปลือกหรือปลอก แล้วแต่อันไหนใหญ่กว่า
    assert math.isclose(z, 2 * max(p["r_out"], p["ring_od_in"] / 2), abs_tol=TOL)
    # เป็นเปลือกผนังบาง ปริมาตรจึงน้อยกว่าก้อนตันมาก
    assert part.volume < x * y * z * 0.15
    assert_watertight(part, "dual_ring_bar", tmp_path)


def test_dual_ring_bar_strap_section(tmp_path):
    """สายคาดที่ตัดมาปริ้นทดสอบต้องบางตามผนังจริงและวางราบพร้อมปริ้น"""
    mod = load_part("dual_ring_bar")
    p = dict(mod.PARAMS, section="strap")
    strap = mod.build(p)["strap"]
    x, y, z = bbox(strap)
    assert math.isclose(x, 2 * p["flare_x"], abs_tol=TOL)
    # ความสูงรวม = ผนัง + ระยะโก่งของส่วนโค้ง ต้องไม่เกินรัศมี
    rise = p["r_out"] * (1 - math.cos(math.radians(p["strap_ang"])))
    assert math.isclose(z, p["wall"] + rise, abs_tol=0.15)
    assert math.isclose(strap.bounding_box().min.Z, 0.0, abs_tol=TOL)  # ก้นแตะเตียง
    assert_watertight(strap, "dual_ring_bar_strap", tmp_path)


def test_dual_ring_bar_flat_section(tmp_path):
    """ชิ้นแบนทดสอบ: กว้างเท่าความยาวส่วนโค้งที่คลี่ออก และเจาะรูครบ"""
    mod = load_part("dual_ring_bar")
    p = dict(mod.PARAMS, section="flat")
    flat = mod.build(p)["flat"]
    x, y, z = bbox(flat)
    # ความกว้าง = ความยาวส่วนโค้ง 2·r·θ ไม่ใช่ระยะคอร์ด 2·r·sin(θ)
    assert math.isclose(y, 2 * p["r_out"] * math.radians(p["strap_ang"]), abs_tol=TOL)
    assert math.isclose(z, p["flat_t"], abs_tol=TOL)
    assert flat.volume < x * y * z * 0.85          # รู/สลอตถูกเจาะจริง
    assert_watertight(flat, "dual_ring_bar_flat", tmp_path)


def test_dual_ring_bar_flat_encloses_every_feature():
    """ทุกช่องต้องอยู่ในเนื้อชิ้นเต็มรูป ไม่มีช่องไหนถูกขอบชิ้นตัดขาด"""
    mod = load_part("dual_ring_bar")
    p = dict(mod.PARAMS, section="flat")
    flat = mod.build(p)["flat"]
    lo, hi = mod._feature_span(p)
    half = bbox(flat)[0] / 2
    assert half >= max(abs(lo), hi) + p["flat_margin"] - TOL


def test_dual_ring_bar_flat_matches_curved_hole_positions():
    """หัวใจของชิ้นทดสอบ: ตำแหน่งรูตามแนวยาวต้องตรงกับชิ้นโค้งจริงเป๊ะ"""
    mod = load_part("dual_ring_bar")
    p = dict(mod.PARAMS)
    flat = mod.build(dict(p, section="flat"))["flat"]
    full = mod.build(dict(p, section="full"))
    # ทั้งคู่จัดกึ่งกลางที่ x=0 จึงเทียบตำแหน่งผิวรูตามแกน X ได้ตรง ๆ
    # กรองด้วยขนาดหน้า: ผิวของช่องเจาะเล็กกว่ารัศมีเปลือก ส่วนผิวเปลือก/รูปลอกใหญ่กว่า
    def hole_faces(part):
        return sorted(round(f.center().X, 3) for f in part.faces()
                      if f.geom_type == GeomType.CYLINDER
                      and max(f.bounding_box().size) < p["r_out"])
    assert hole_faces(flat) == hole_faces(full)


def test_dual_ring_bar_custom(tmp_path):
    mod = load_part("dual_ring_bar")
    p = dict(mod.PARAMS, length=150.0, flare_x=50.0, ring_x=66.0,
             vent_n=0, slot_l=30.0, vslot_n=0, fit="slide")
    part = mod.build(p)
    x, y, z = bbox(part)
    assert math.isclose(x, 150.0, abs_tol=TOL)
    assert_watertight(part, "dual_ring_bar_custom", tmp_path)


def test_dual_ring_bar_thin_wall():
    mod = load_part("dual_ring_bar")
    p = dict(mod.PARAMS, ring_bore=56.0, ring_od_out=56.4)
    with pytest.raises(ValueError):
        mod.build(p)


def test_dual_ring_bar_bad_section():
    mod = load_part("dual_ring_bar")
    with pytest.raises(ValueError):
        mod.build(dict(mod.PARAMS, section="nope"))


def test_fdm_hole_compensation():
    # รูสำหรับแกน 8 mm แบบ slide ต้องใหญ่กว่าแกนจริงเสมอ
    d = fdm.hole_dia(8.0, fdm.FIT_SLIDE)
    assert d == pytest.approx(8.0 + fdm.HOLE_COMP + 2 * fdm.FIT_SLIDE)
    assert d > 8.0
