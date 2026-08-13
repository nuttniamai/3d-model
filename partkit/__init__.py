"""PartKit — ชุดเครื่องมือ Python สร้างชิ้นส่วน 3D แบบ true-to-scale (หน่วย mm)
สำหรับปริ้นกับเครื่อง FDM เช่น Bambu Lab P2S
"""
from . import fdm
from .fasteners import (
    METRIC,
    clearance_hole,
    counterbore_hole,
    countersunk_hole,
    heat_set_pocket,
    hex_nut_pocket,
    tap_hole,
)
from .export import export_part
from .cli import run_cli

__all__ = [
    "fdm", "METRIC",
    "clearance_hole", "tap_hole", "counterbore_hole", "countersunk_hole",
    "hex_nut_pocket", "heat_set_pocket",
    "export_part", "run_cli",
]
