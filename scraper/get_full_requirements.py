"""
Merge CAS Core requirements + a program's track-specific requirements
into a single output for any (program_slug, track) combination.

Usage:
    python get_full_requirements.py mathematics-ba
    python get_full_requirements.py economics-ba --track Theory
    python get_full_requirements.py biology-ba --track Ecology --json /tmp/full.json
    python get_full_requirements.py biology-ba --track Ecology --format pretty
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv


def load_from_mongo(program_slug: str, track: str | None) -> tuple[dict, dict]:
    from pymongo import MongoClient

    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGO_DB", "nyu_bulletins")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]

    program = db["cas_programs"].find_one({"program_slug": program_slug, "track": track})
    if not program:
        # Maybe user passed wrong track; show available
        avail = list(db["cas_programs"].find({"program_slug": program_slug}, {"track": 1}))
        if avail:
            tracks = [a.get("track") for a in avail]
            raise SystemExit(
                f"No document for program_slug={program_slug!r} track={track!r}. "
                f"Available tracks: {tracks}"
            )
        raise SystemExit(f"No document for program_slug={program_slug!r}")

    core = db["cas_core"].find_one({"_id": "cas_core"})
    if not core:
        raise SystemExit("cas_core collection is empty — run scrape_core.py first")

    return program, core


def merge(program: dict, core: dict) -> dict:
    """Combine into a single self-contained payload."""
    return {
        "program_slug": program["program_slug"],
        "program_name": program["program_name"],
        "degree": program.get("degree"),
        "track": program.get("track"),
        "url": program.get("url"),
        "merged_at": datetime.now(timezone.utc).isoformat(),
        "cas_core_requirements": {
            "name": core["name"],
            "url": core["url"],
            "components": core["components"],
        },
        "program_common_sections": program.get("common_sections", []),
        "program_sections": program.get("sections", []),
    }


def _print_section(s: dict, indent: str = "  ") -> None:
    header = s.get("header") or "(no header)"
    print(f"{indent}## {header}")
    for c in s.get("courses", []):
        code = (c.get("code") or "—").ljust(18)
        title = (c.get("title") or "")[:55].ljust(55)
        cred = c.get("credits") or ""
        or_mark = " [or]" if c.get("is_or_alternative") else ""
        ind = "  " * (c.get("indent_level") or 0)
        if c.get("comment"):
            print(f"{indent}    {ind}# {c['comment'][:80]}")
        else:
            print(f"{indent}    {ind}{code} {title} {cred}{or_mark}")


def render_pretty(merged: dict) -> None:
    print("=" * 78)
    print(f"  {merged['program_name']}  [degree={merged['degree']}, track={merged['track'] or '—'}]")
    print(f"  {merged['url']}")
    print("=" * 78)

    # --- CAS Core ---
    core = merged["cas_core_requirements"]
    print(f"\n┌─ CAS CORE REQUIREMENTS ({core['name']}) ───────────────────────")
    current_parent: str | None = None
    for comp in core["components"]:
        parent = comp.get("parent")
        if parent != current_parent:
            current_parent = parent
        prefix = "│  " + ("  └ " if parent else "")
        cred = f"  ({comp['credits']} cr)" if comp.get("credits") else ""
        pat = f"  ⟦{comp['code_pattern']}⟧" if comp.get("code_pattern") else ""
        codes_n = len(comp.get("course_codes") or [])
        codes_hint = f"  [{codes_n} courses listed]" if codes_n else ""
        print(f"{prefix}● {comp['category']}{cred}{pat}{codes_hint}")
    print("└" + "─" * 70)

    # --- Program common sections ---
    if merged.get("program_common_sections"):
        print(f"\n┌─ PROGRAM COMMON SECTIONS ────────────────────────────────────")
        for s in merged["program_common_sections"]:
            _print_section(s, indent="│ ")
        print("└" + "─" * 70)

    # --- Program track-specific (or main) sections ---
    label = "PROGRAM TRACK" if merged["track"] else "PROGRAM SECTIONS"
    if merged["track"]:
        label += f" ({merged['track']})"
    print(f"\n┌─ {label} ──────────────────────────────────────")
    for s in merged.get("program_sections", []):
        _print_section(s, indent="│ ")
    print("└" + "─" * 70)


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("program_slug", help="e.g. mathematics-ba, economics-ba")
    ap.add_argument("--track", default=None, help="track name; omit for no-track programs")
    ap.add_argument("--json", help="dump merged result to JSON file")
    ap.add_argument("--format", choices=("pretty", "json"), default="pretty",
                    help="stdout format (default: pretty)")
    args = ap.parse_args()

    program, core = load_from_mongo(args.program_slug, args.track)
    merged = merge(program, core)

    if args.format == "json":
        print(json.dumps(merged, indent=2, default=str, ensure_ascii=False))
    else:
        render_pretty(merged)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, default=str, ensure_ascii=False)
        print(f"\n[info] dumped JSON → {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
