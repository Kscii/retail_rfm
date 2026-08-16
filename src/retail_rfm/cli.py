from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .constants import DEFAULT_CSV, DEFAULT_EVIDENCE_ROOT, DEFAULT_OUTPUT_DIR


def _common_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="read-only source CSV")
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="generated artifact directory"
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=DEFAULT_EVIDENCE_ROOT,
        help="validated exploration evidence root",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="retail-rfm")
    subcommands = parser.add_subparsers(dest="command", required=True)
    build = subcommands.add_parser("build", help="build model, SQLite and integrity artifacts")
    _common_paths(build)
    verify = subcommands.add_parser("verify", help="verify data, model and SQLite artifacts")
    _common_paths(verify)
    verify.add_argument(
        "--deep", action="store_true", help="recompute k and sensitivity evidence without mutation"
    )
    dashboard = subcommands.add_parser("dashboard", help="run the localhost Dash application")
    dashboard.add_argument(
        "--db", type=Path, default=DEFAULT_OUTPUT_DIR / "retail_rfm.sqlite", help="SQLite path"
    )
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8050)
    presentation = subcommands.add_parser(
        "export-presentation", help="export the audited static presentation dataset"
    )
    presentation.add_argument(
        "--csv", type=Path, default=DEFAULT_CSV, help="read-only source CSV"
    )
    presentation.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "retail_rfm.sqlite",
        help="verified SQLite artifact",
    )
    presentation.add_argument(
        "--output-dir",
        type=Path,
        default=Path("presentation/public/static-demo"),
        help="static presentation output directory",
    )
    presentation.add_argument(
        "--evidence-root",
        type=Path,
        default=DEFAULT_EVIDENCE_ROOT,
        help="validated exploration evidence root",
    )
    return parser


def run(args: argparse.Namespace) -> dict | None:
    if args.command == "build":
        from .pipeline import build_artifacts

        result = build_artifacts(args.csv, args.output_dir, args.evidence_root)
        return {"status": "PASS", **result}
    if args.command == "verify":
        from .verification import verify_artifacts

        result = verify_artifacts(args.csv, args.output_dir, args.evidence_root)
        if args.deep:
            from .deep_verification import deep_verify

            result["deep"] = deep_verify(args.csv, args.evidence_root)
        return result
    if args.command == "dashboard":
        from .dashboard.app import create_app

        app = create_app(args.db)
        app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
        return None
    if args.command == "export-presentation":
        from .presentation_export import export_presentation

        return export_presentation(args.csv, args.db, args.output_dir, args.evidence_root)
    raise ValueError(args.command)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run(args)
        if result is not None:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    except KeyboardInterrupt:
        raise
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
