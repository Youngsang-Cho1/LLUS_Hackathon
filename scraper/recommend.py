"""
Recommend next courses to take, ranked by:
  1. Prerequisite readiness (all prereqs met → top)
  2. Best-rated professor (if RMP data available for known instructors)
  3. Course number ascending

Pulls from:
  - cas_programs / cas_core (requirements)
  - course_catalog (prereqs + descriptions)
  - rmp_cache (professor ratings)
  - the parsed transcript (StudentState)

Without live offering data (Albert is reCAPTCHA-protected), professor names
must be supplied manually via --instructors  "CSCI-UA 310:Khoda,Shasha;CSCI-UA 473:LeCun"
or via a JSON file (`--instructors-file`).

Usage:
    python recommend.py /path/to/transcript.pdf
    python recommend.py /path/to/transcript.pdf --skip "Foreign Language"
    python recommend.py /path/to/transcript.pdf \
        --instructors "CSCI-UA 310:Shasha,Khoda;CSCI-UA 473:LeCun"
    python recommend.py /path/to/transcript.pdf --max-credits 18
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from get_full_requirements import load_from_mongo, merge
from parse_transcript import parse_transcript
from requirement_diff import compute_diff, _slug_from_program_name
from rmp_client import ProfessorRating, RMPClient
from student_state import StudentState, build_state_from_parse


@dataclass
class Recommendation:
    code: str
    title: str | None
    credits: float | None
    section: str        # which requirement section it satisfies
    prereqs_met: bool
    prereq_codes: list[str]
    missing_prereqs: list[str]
    instructors: list[ProfessorRating] = field(default_factory=list)
    best_rating: float | None = None
    score: float = 0.0
    reason: str = ""


def _course_credits_to_float(credits_str: str | None) -> float | None:
    if not credits_str:
        return None
    s = str(credits_str).split("-")[0].strip()
    try:
        return float(s)
    except ValueError:
        return None


def _load_catalog():
    """Return {course_code: catalog_doc} from MongoDB, or empty dict."""
    try:
        from pymongo import MongoClient
        uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.environ.get("MONGO_DB", "nyu_bulletins")
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        return {d["code"]: d for d in client[db_name]["course_catalog"].find()}
    except Exception as e:
        print(f"[warn] course_catalog unavailable: {e}", file=sys.stderr)
        return {}


def _parse_instructors_arg(arg: str | None, file_path: str | None) -> dict[str, list[str]]:
    """Format: 'CODE:Name1,Name2;CODE2:Name3'  →  {CODE: [Name1, Name2], ...}"""
    out: dict[str, list[str]] = {}
    if file_path:
        with open(file_path) as f:
            data = json.load(f)
            for k, v in data.items():
                out.setdefault(k, []).extend(v if isinstance(v, list) else [v])
    if arg:
        for chunk in arg.split(";"):
            chunk = chunk.strip()
            if not chunk or ":" not in chunk:
                continue
            code, names = chunk.split(":", 1)
            for n in names.split(","):
                n = n.strip()
                if n:
                    out.setdefault(code.strip(), []).append(n)
    return out


def _evaluate_prereqs(prereq_text: str | None, prereq_codes: list[str],
                      state: StudentState) -> tuple[bool, list[str]]:
    """Return (prereqs_met, missing_prereqs).
    Approximates AND/OR logic from the raw prereq_text:
      - No prereqs → met
      - All codes satisfied → met
      - Some codes satisfied AND text has 'OR' but no 'AND' → met (any-of)
      - Otherwise → not met (returns codes the student is missing)
    """
    if not prereq_codes:
        return True, []
    missing = [c for c in prereq_codes if not state.has(c)]
    if not missing:
        return True, []
    if not prereq_text:
        return False, missing
    text_upper = prereq_text.upper()
    has_and = " AND " in text_upper
    has_or = " OR " in text_upper
    if has_or and not has_and and len(missing) < len(prereq_codes):
        # Pure OR alternative satisfied by at least one course
        return True, []
    return False, missing


def _collect_missing_courses(diff_obj, catalog: dict, state: StudentState) -> list[Recommendation]:
    """Walk diff results and produce candidate Recommendation entries."""
    out: list[Recommendation] = []
    seen: set[str] = set()

    def _process(section_label: str, section):
        for c in section.courses:
            if c.code is None or c.status != "missing":
                continue
            if c.code in seen:
                continue
            seen.add(c.code)

            cat = catalog.get(c.code, {})
            prereq_codes = cat.get("prereq_codes", []) or []
            prereqs_met, missing_prereqs = _evaluate_prereqs(
                cat.get("prereq_text"), prereq_codes, state,
            )

            credits_val = _course_credits_to_float(c.credits) or _course_credits_to_float(cat.get("credits"))

            out.append(Recommendation(
                code=c.code,
                title=c.title or cat.get("title"),
                credits=credits_val,
                section=section_label,
                prereqs_met=prereqs_met,
                prereq_codes=prereq_codes,
                missing_prereqs=missing_prereqs,
            ))

    for s in diff_obj.common:
        _process(s.header or "common", s)
    for s in diff_obj.track_sections:
        _process(s.header or "track", s)
    return out


def _rate_instructors(rmp: RMPClient, recs: list[Recommendation],
                      mapping: dict[str, list[str]]) -> None:
    """Populate Recommendation.instructors from RMP."""
    for r in recs:
        names = mapping.get(r.code, [])
        if not names:
            continue
        # Department hint from the course subject prefix (CSCI-UA → "Computer Science")
        dept_hint = _subject_to_dept(r.code)
        for n in names:
            p = rmp.best_match(n, department=dept_hint)
            if p:
                r.instructors.append(p)
        r.instructors.sort(key=lambda p: (p.avg_rating or 0), reverse=True)
        if r.instructors:
            r.best_rating = r.instructors[0].avg_rating


SUBJECT_DEPT_HINTS = {
    "CSCI-UA": "Computer Science",
    "DS-UA":   "Data Science",
    "MATH-UA": "Mathematics",
    "PHYS-UA": "Physics",
    "CHEM-UA": "Chemistry",
    "BIOL-UA": "Biology",
    "ECON-UA": "Economics",
    "PSYCH-UA": "Psychology",
    "EXPOS-UA": "Expository Writing",
    "PHIL-UA": "Philosophy",
}


def _subject_to_dept(code: str) -> str | None:
    parts = code.split()
    return SUBJECT_DEPT_HINTS.get(parts[0]) if parts else None


def _score_and_rank(recs: list[Recommendation]) -> None:
    """Compute a score per recommendation. Higher = recommend more."""
    for r in recs:
        # Base: 100 if prereqs met, else 0 (still listed but at bottom)
        score = 100.0 if r.prereqs_met else 0.0
        # Add up to 50 for prof rating (5.0 → +50)
        if r.best_rating is not None:
            score += r.best_rating * 10
            r.reason = f"prereqs ✓, prof rating {r.best_rating:.2f}"
        else:
            r.reason = "prereqs ✓" if r.prereqs_met else f"missing prereqs: {', '.join(r.missing_prereqs)}"
        # Slight bias toward lower course numbers (intro courses first)
        try:
            num = int("".join(ch for ch in r.code.split()[1] if ch.isdigit()))
            score -= num * 0.001
        except (ValueError, IndexError):
            pass
        r.score = score
    recs.sort(key=lambda r: r.score, reverse=True)


def _greedy_pack(recs: list[Recommendation], max_credits: float) -> list[Recommendation]:
    """Pick top recommendations whose total credits ≤ max_credits.
    Only picks courses whose prereqs are met."""
    chosen: list[Recommendation] = []
    used = 0.0
    for r in recs:
        if not r.prereqs_met:
            continue
        c = r.credits or 4.0
        if used + c > max_credits:
            continue
        chosen.append(r)
        used += c
    return chosen


def render(recs: list[Recommendation], chosen: list[Recommendation], max_credits: float) -> None:
    print(f"\n{'='*78}")
    print(f"  RECOMMENDED COURSES  (top picks ≤ {max_credits} credits)")
    print(f"{'='*78}")
    if not chosen:
        print("  (no courses with all prereqs met — see full list below)")
    else:
        total = 0.0
        for r in chosen:
            cr = r.credits or 0
            total += cr
            rating = f"{r.best_rating:.2f}★" if r.best_rating else "—"
            instr = ", ".join(p.name for p in r.instructors) or "—"
            print(f"  ★ {r.code:<14} {(r.title or '')[:38]:<38} {cr:>4}cr  rating={rating:<5}  via {r.section}")
            print(f"     instructors: {instr}")
        print(f"\n  Total: {total} credits")

    print(f"\n┌─ ALL MISSING COURSES (sorted by score)")
    for r in recs:
        icon = "✅" if r.prereqs_met else "🔒"
        cr = r.credits or 0
        title = (r.title or "")[:36]
        rating = f"{r.best_rating:.2f}★" if r.best_rating else ""
        print(f"│ {icon} {r.code:<14} {title:<36} {cr:>4}cr  {rating:>6}  ({r.reason})")


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--slug", help="program slug (default: inferred)")
    ap.add_argument("--track", default=None)
    ap.add_argument("--skip", action="append", default=[])
    ap.add_argument("--instructors", help="format: 'CODE:Name1,Name2;CODE2:Name3'")
    ap.add_argument("--instructors-file", help="JSON: {CODE: [names]}")
    ap.add_argument("--max-credits", type=float, default=18.0)
    ap.add_argument("--json", help="dump full result")
    args = ap.parse_args()

    parse = parse_transcript(args.pdf)
    state = build_state_from_parse(parse)

    slug = args.slug
    if not slug:
        if not parse.current_program or not parse.current_program.majors:
            print("[err] couldn't infer slug; pass --slug", file=sys.stderr)
            return 2
        major_name = parse.current_program.majors[0]
        degree_token = "ba" if (parse.current_program.degree or "").lower().startswith(
            "bachelor of arts") else "bs"
        slug = _slug_from_program_name(major_name + " " + degree_token)
        print(f"[info] inferred slug: {slug}")

    program, core = load_from_mongo(slug, args.track)
    merged = merge(program, core)
    diff = compute_diff(state, merged, skips=args.skip)

    catalog = _load_catalog()
    print(f"[info] course_catalog: {len(catalog)} entries")

    recs = _collect_missing_courses(diff, catalog, state)

    instr_map = _parse_instructors_arg(args.instructors, args.instructors_file)
    if instr_map:
        rmp = RMPClient()
        _rate_instructors(rmp, recs, instr_map)
        print(f"[info] rated instructors for {len(instr_map)} courses")

    _score_and_rank(recs)
    chosen = _greedy_pack(recs, args.max_credits)

    render(recs, chosen, args.max_credits)

    if args.json:
        payload = {
            "program_slug": slug,
            "track": args.track,
            "all_missing": [asdict(r) for r in recs],
            "top_picks": [asdict(r) for r in chosen],
        }
        with open(args.json, "w") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"\n[info] dumped → {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
