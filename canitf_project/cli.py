from __future__ import annotations

import argparse
import pathlib

from .cdktn import generate_cdktn_source
from .github import fetch_releases, releases_from_json, releases_to_json
from .parser import extract_candidates_from_release, merge_candidates
from .table import load_canitf_features, rows_to_json, rows_to_markdown


def cmd_fetch(args: argparse.Namespace) -> int:
    releases = fetch_releases(per_page=args.per_page, max_pages=args.max_pages)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(releases_to_json(releases), encoding="utf-8")
    print(f"wrote {len(releases)} releases to {out}")
    return 0


def cmd_build_table(args: argparse.Namespace) -> int:
    releases = releases_from_json(pathlib.Path(args.input).read_text(encoding="utf-8"))
    candidates = []
    for rel in releases:
        candidates.extend(extract_candidates_from_release(rel.tool, rel.tag, rel.html_url, rel.body))
    if args.include_canitf:
        candidates.extend(load_canitf_features())
    rows = merge_candidates(candidates)
    if args.json_out:
        path = pathlib.Path(args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rows_to_json(rows), encoding="utf-8")
        print(f"wrote {len(rows)} feature rows to {path}")
    if args.markdown_out:
        path = pathlib.Path(args.markdown_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rows_to_markdown(rows), encoding="utf-8")
        print(f"wrote Markdown table to {path}")
    if not args.json_out and not args.markdown_out:
        print(rows_to_markdown(rows))
    return 0


def cmd_inspect_canitf(args: argparse.Namespace) -> int:
    rows = load_canitf_features()
    both = sum(1 for r in rows if "terraform" in r.tools and "opentofu" in r.tools)
    print(f"cani.tf API rows: {len(rows)} total; {both} have both tools; source: https://cani.tf/tools.json")
    return 0


def cmd_generate_cdktn_source(args: argparse.Namespace) -> int:
    generate_cdktn_source(
        features_input_path=args.features_input,
        out_path=args.out,
        generated_features_path=args.generated_features,
        baseline=args.baseline,
    )
    print(f"wrote CDK Terrain source to {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="canitf", description="Terraform/OpenTofu feature tracking from official release notes")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("fetch", help="download official GitHub release notes")
    p.add_argument("--out", default="data/releases.json")
    p.add_argument("--per-page", type=int, default=100)
    p.add_argument("--max-pages", type=int, default=3)
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("build-table", help="extract candidate features and write a comparison table")
    p.add_argument("--input", default="data/releases.json")
    p.add_argument("--json-out")
    p.add_argument("--markdown-out")
    p.add_argument("--include-canitf", action="store_true", help="merge curated cani.tf rows from https://cani.tf/tools.json")
    p.set_defaults(func=cmd_build_table)

    p = sub.add_parser("inspect-canitf", help="check the public cani.tf JSON API")
    p.set_defaults(func=cmd_inspect_canitf)

    p = sub.add_parser("generate-cdktn-source", help="generate a CDK Terrain TypeScript feature constraint source file")
    p.add_argument("--features-input", default="data/hcl-feature-input.json", help="human-curated feature input JSON")
    p.add_argument("--generated-features", default="data/features.json", help="generated feature rows used to fill missing fields")
    p.add_argument("--out", default="data/cdktn-feature-constraints.ts")
    p.add_argument("--baseline", default=None, help="comparison baseline version, defaults to the input file baseline")
    p.set_defaults(func=cmd_generate_cdktn_source)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
