"""CLI กลางสำหรับไฟล์ part ทุกไฟล์

ใช้ในไฟล์ part แบบนี้:

    PARAMS = dict(width=20.0, height=10.0)

    def build(p):
        ...
        return part  # หรือ dict {"ชื่อย่อย": part} ถ้ามีหลายชิ้น

    if __name__ == "__main__":
        from partkit.cli import run_cli
        run_cli(build, PARAMS, "my_part")

แล้วรัน:  python parts/my_part.py --width 25 --out out/
"""
import argparse

from .export import export_part


def run_cli(build_fn, params: dict, name: str):
    parser = argparse.ArgumentParser(
        description=f"สร้างโมเดล {name} (หน่วย mm ทั้งหมด)")
    for key, val in params.items():
        arg = "--" + key.replace("_", "-")
        if isinstance(val, bool):
            parser.add_argument(arg, type=lambda s: s.lower() in ("1", "true", "yes"),
                                default=val, help=f"(default: {val})")
        elif isinstance(val, (int, float)):
            parser.add_argument(arg, type=float, default=float(val),
                                help=f"(default: {val})")
        else:
            parser.add_argument(arg, type=str, default=val, help=f"(default: {val})")
    parser.add_argument("--out", default="out", help="โฟลเดอร์ปลายทาง (default: out)")
    parser.add_argument("--no-check", action="store_true",
                        help="ข้ามการตรวจ mesh watertight")
    args = parser.parse_args()

    p = {key: getattr(args, key) for key in params}
    result = build_fn(p)

    if not isinstance(result, dict):
        result = {name: result}
    for part_name, part in result.items():
        full = part_name if part_name == name else f"{name}_{part_name}"
        export_part(part, full, out_dir=args.out, check=not args.no_check)
