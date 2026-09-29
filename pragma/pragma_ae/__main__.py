"""CLI: python3 -m pragma_ae {locate,validate,freeze,sheet,preflight} …  (ejecutar desde pragma/)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import inventory as inv


def cmd_locate(args):
    from .imageio import locate_image
    path = locate_image(args.image)
    print(json.dumps({"image": str(path), "sha256": inv.sha256_file(path)}, indent=2))


def cmd_validate(args):
    data = inv.load(args.inventory)
    result = inv.validate(data, Path(args.inventory).parent)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not result["errors"] else 2


def cmd_freeze(args):
    data = inv.load(args.inventory)
    try:
        frozen = inv.freeze(data, Path(args.inventory).parent, frozen_by=args.frozen_by)
    except ValueError as exc:
        print(f"NO CONGELADO: {exc}", file=sys.stderr)
        return 2
    Path(args.out).write_text(json.dumps(frozen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": args.out, "content_sha256": frozen["freeze"]["content_sha256"]}, indent=2))


def cmd_sheet(args):
    from .imageio import load_rgb, locate_image
    from .sheet import legend_markdown, numbered_sheet
    data = inv.load(args.inventory)
    image = load_rgb(locate_image(args.image))
    shown = numbered_sheet(image, data["objects"], args.out, tiers=tuple(args.tiers))
    legend = Path(args.out).with_suffix(".md")
    legend.write_text(legend_markdown(shown), encoding="utf-8")
    print(json.dumps({"sheet": args.out, "legend": str(legend), "objects": len(shown)}, indent=2))


def cmd_preflight(args):
    from .imageio import load_rgb, locate_image
    from .preflight import sentinel_contact_sheet, specs_from_notebook
    notebook = json.loads(Path(args.notebook).read_text(encoding="utf-8"))
    specs, box = specs_from_notebook(notebook)
    image = load_rgb(locate_image(args.image))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = sentinel_contact_sheet(image, specs, out_dir / "contact_sheet.png")
    payload = {"notebook": args.notebook, "notebook_sha256": inv.sha256_file(args.notebook),
               "box_xyxy": box, "sentinels": stats}
    (out_dir / "contact_sheet.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "sentinels": len(stats), "box_xyxy": box}, indent=2))


def cmd_audit_aem1(args):
    from .aem1_audit import audit_zip
    from .imageio import load_rgb, locate_image
    try:
        photo = load_rgb(locate_image(args.image))
    except FileNotFoundError as exc:
        print(f"AVISO: sin foto ({exc}); solo se verifica integridad.", file=sys.stderr)
        photo = None
    out_dir = Path(args.out_dir or Path("local") / "audit" / Path(args.zip).stem)
    result = audit_zip(args.zip, photo=photo, out_dir=out_dir)
    summary = {
        "out_dir": str(out_dir), "run_kind": result["run_kind"], "integrity": result["integrity"],
        "candidates": len(result["candidates"]),
        "sentinel_screen_pass": [f"{c['key']}#{c['candidate_index']}" for c in result["candidates"] if c["sentinel_screen_pass"]],
        "inspection_order": result["inspection_order"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if result["integrity"]["pass"] else 2


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pragma_ae")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("locate", help="busca la foto de aceptación por SHA-256")
    p.add_argument("--image")
    p.set_defaults(func=cmd_locate)
    p = sub.add_parser("validate", help="valida un scene_inventory y deriva su estado A-E0")
    p.add_argument("inventory")
    p.set_defaults(func=cmd_validate)
    p = sub.add_parser("freeze", help="congela un inventario HUMAN_REVIEWED listo")
    p.add_argument("inventory")
    p.add_argument("--out", required=True)
    p.add_argument("--frozen-by", required=True)
    p.set_defaults(func=cmd_freeze)
    p = sub.add_parser("sheet", help="lámina numerada (local; deriva de la foto)")
    p.add_argument("inventory")
    p.add_argument("--image")
    p.add_argument("--out", default="local/lamina_A-E0.png")
    p.add_argument("--tiers", nargs="+", default=["A", "B", "C"])
    p.set_defaults(func=cmd_sheet)
    p = sub.add_parser("preflight", help="hoja de contactos de sentinelas de un cuaderno A-E(−1)")
    p.add_argument("notebook")
    p.add_argument("--image")
    p.add_argument("--out-dir", default="local/preflight")
    p.set_defaults(func=cmd_preflight)
    p = sub.add_parser("audit-aem1", help="auditoría IA automática del ZIP de A-E(−1)")
    p.add_argument("zip")
    p.add_argument("--image")
    p.add_argument("--out-dir")
    p.set_defaults(func=cmd_audit_aem1)
    args = parser.parse_args(argv)
    Path("local").mkdir(exist_ok=True) if args.command in ("sheet", "preflight") else None
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
