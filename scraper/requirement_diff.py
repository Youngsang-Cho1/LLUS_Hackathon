"""
Compute the requirement diff between a student's state and a (program, track).

Given:
  - merged requirements (from get_full_requirements.py)
  - StudentState (from student_state.py)

Produce:
  - Per-section breakdown: which courses are satisfied, which are missing
  - "or" alternatives: any one of an or-group counts
  - CAS Core: which categories are satisfied (via AP / explicit course / pattern match)
  - Summary: total credits required vs. covered, % completion

Usage:
    python requirement_diff.py /path/to/transcript.pdf [--track TRACK]
    # auto-uses current_program from the transcript

    python requirement_diff.py /path/to/transcript.pdf --slug computer-data-science-ba
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from get_full_requirements import load_from_mongo, merge
from parse_transcript import parse_transcript
from student_state import StudentState, build_state_from_parse


@dataclass
class CourseStatus:
    code: str | None
    title: str | None
    credits: str | None
    status: str          # "satisfied" | "in_progress" | "missing" | "info"
    via: str | None      # "completed" | "ap" | "transfer" | "in_progress" | None
    is_or_alternative: bool = False


@dataclass
class SectionDiff:
    header: str | None
    courses: list[CourseStatus]
    section_satisfied: bool   # all required (non-or) covered
    n_required: int           # codes that need to be done (excluding "or" groups)
    n_done: int


@dataclass
class CoreComponentDiff:
    category: str
    parent: str | None
    code_pattern: str | None
    credits: str | None
    status: str           # "satisfied" | "in_progress" | "missing"
    via: str | None       # "ap" | "course_match" | None


@dataclass
class RequirementDiff:
    program_slug: str
    program_name: str
    track: str | None
    cas_core: list[CoreComponentDiff]
    common: list[SectionDiff]
    track_sections: list[SectionDiff]
    summary: dict


def _normalize_code(c: str | None) -> str | None:
    if not c:
        return None
    # Collapse whitespace (page text uses NBSP between subject and number)
    return re.sub(r"\s+", " ", c).strip()


def _diff_section(section: dict, state: StudentState, skips: set[str]) -> SectionDiff:
    courses_out: list[CourseStatus] = []
    n_required = 0
    n_done = 0

    section_header = section.get("header") or ""
    section_skipped = section_header in skips

    for c in section.get("courses", []):
        code = _normalize_code(c.get("code"))
        title = c.get("title")
        credits = c.get("credits")
        is_or = bool(c.get("is_or_alternative"))

        if not code:
            courses_out.append(CourseStatus(
                code=None, title=title, credits=credits,
                status="info", via=None,
            ))
            continue

        # Decide status — skip overrides everything else
        via: str | None = None
        if section_skipped or code in skips:
            status, via = "skipped", "manual"
        elif code in state.completed_codes:
            status, via = "satisfied", "completed"
        elif code in state.satisfied_by_ap:
            status, via = "satisfied", "ap"
        elif code in state.satisfied_by_transfer:
            status, via = "satisfied", "transfer"
        elif code in state.in_progress_codes:
            status, via = "in_progress", "in_progress"
        else:
            status = "missing"

        courses_out.append(CourseStatus(
            code=code, title=title, credits=credits,
            status=status, via=via, is_or_alternative=is_or,
        ))

    # Compute n_required / n_done with "or" group logic.
    # Treat consecutive courses where one is_or_alternative=True as one "group":
    # the group is satisfied if ANY member is satisfied/in-progress/skipped.
    i = 0
    while i < len(courses_out):
        c = courses_out[i]
        if c.code is None:
            i += 1
            continue
        group = [c]
        j = i + 1
        while j < len(courses_out) and courses_out[j].is_or_alternative:
            group.append(courses_out[j])
            j += 1
        n_required += 1
        if any(g.status in ("satisfied", "in_progress", "skipped") for g in group):
            n_done += 1
        i = j

    section_satisfied = (n_required > 0 and n_done == n_required) or n_required == 0
    return SectionDiff(
        header=section.get("header"),
        courses=courses_out,
        section_satisfied=section_satisfied,
        n_required=n_required,
        n_done=n_done,
    )


def _code_matches_pattern(code: str, pattern: str) -> bool:
    """Pattern matching:
      - 'CORE-UA 4XX' (wildcard X in NUMBER portion) → CORE-UA 400..499
      - 'FYSEM-UA' (subject only) → any FYSEM-UA *
      - 'EXPOS-UA 1' (literal full code) → exact match only
    Note: must NOT confuse the X in 'EXPOS-UA' as a wildcard.
    """
    code = re.sub(r"\s+", " ", code).strip()
    parts = pattern.strip().split(None, 1)

    if len(parts) == 1:
        # subject-only prefix match
        return code.upper().startswith(parts[0].upper() + " ")

    subject, number = parts
    if "X" in number.upper():
        # wildcard regex: only X in NUMBER part is treated as \d
        num_rgx = re.escape(number).replace("X", r"\d").replace("x", r"\d")
        rgx = re.escape(subject) + r"\s+" + num_rgx
        return bool(re.fullmatch(rgx, code, flags=re.IGNORECASE))

    # literal: exact match
    return code.upper() == pattern.upper().replace("  ", " ")


def _diff_core(core_components: list[dict], state: StudentState, skips: set[str]) -> list[CoreComponentDiff]:
    out: list[CoreComponentDiff] = []
    for comp in core_components:
        category = comp["category"]
        pattern = comp.get("code_pattern")
        parent = comp.get("parent")
        credits = comp.get("credits")

        # Manual skip overrides
        if category in skips:
            out.append(CoreComponentDiff(
                category=category, parent=parent,
                code_pattern=pattern, credits=credits,
                status="skipped", via="manual",
            ))
            continue

        # Method 1: explicit AP-based core category satisfaction
        if state.satisfies_core(category):
            out.append(CoreComponentDiff(
                category=category, parent=parent,
                code_pattern=pattern, credits=credits,
                status="satisfied", via="ap",
            ))
            continue

        # Method 2: any completed/transferred course matches the code pattern
        if pattern:
            matched: str | None = None
            in_prog_match: str | None = None
            for code in state.all_satisfied_codes - state.in_progress_codes:
                if _code_matches_pattern(code, pattern):
                    matched = code
                    break
            if matched is None:
                for code in state.in_progress_codes:
                    if _code_matches_pattern(code, pattern):
                        in_prog_match = code
                        break
            if matched:
                out.append(CoreComponentDiff(
                    category=category, parent=parent,
                    code_pattern=pattern, credits=credits,
                    status="satisfied", via="course_match",
                ))
                continue
            if in_prog_match:
                out.append(CoreComponentDiff(
                    category=category, parent=parent,
                    code_pattern=pattern, credits=credits,
                    status="in_progress", via="in_progress",
                ))
                continue

        # Skip parent-only "umbrella" components (FCC, FSI) — they have child
        # categories that we already check individually.
        if not pattern and parent is None and category in (
            "Foundations of Contemporary Culture",
            "Foundations of Scientific Inquiry",
        ):
            continue

        out.append(CoreComponentDiff(
            category=category, parent=parent,
            code_pattern=pattern, credits=credits,
            status="missing", via=None,
        ))
    return out


def compute_diff(state: StudentState, merged: dict, skips: list[str] | None = None) -> RequirementDiff:
    skips_set = set(skips or [])
    core_diff = _diff_core(merged["cas_core_requirements"]["components"], state, skips_set)
    common = [_diff_section(s, state, skips_set) for s in merged.get("program_common_sections", [])]
    track_sections = [_diff_section(s, state, skips_set) for s in merged.get("program_sections", [])]

    # Summary stats
    core_total = sum(1 for c in core_diff if c.status != "info")
    core_done = sum(1 for c in core_diff if c.status in ("satisfied", "skipped"))
    core_in_prog = sum(1 for c in core_diff if c.status == "in_progress")

    sec_total = sum(s.n_required for s in common + track_sections)
    sec_done = sum(s.n_done for s in common + track_sections)

    return RequirementDiff(
        program_slug=merged["program_slug"],
        program_name=merged["program_name"],
        track=merged.get("track"),
        cas_core=core_diff,
        common=common,
        track_sections=track_sections,
        summary={
            "cas_core": {"total": core_total, "satisfied": core_done,
                         "in_progress": core_in_prog,
                         "remaining": core_total - core_done - core_in_prog},
            "program_sections": {"total_codes": sec_total, "satisfied_or_in_progress": sec_done,
                                 "remaining_codes": sec_total - sec_done},
        },
    )


def render(d: RequirementDiff) -> None:
    track_lbl = f" [track: {d.track}]" if d.track else ""
    print(f"\n{'='*78}")
    print(f"  {d.program_name}{track_lbl}")
    print(f"{'='*78}")

    # CAS Core
    s = d.summary["cas_core"]
    print(f"\n┌─ CAS CORE  ({s['satisfied']}/{s['total']} satisfied, "
          f"{s['in_progress']} in-progress, {s['remaining']} remaining)")
    for c in d.cas_core:
        icon = {"satisfied": "✅", "in_progress": "⏳", "missing": "❌", "skipped": "⏭"}[c.status]
        via = f" via {c.via}" if c.via else ""
        parent = f"  ({c.parent}) " if c.parent else "  "
        pat = f"  ⟦{c.code_pattern}⟧" if c.code_pattern else ""
        print(f"│  {icon} {parent}{c.category}{pat}{via}")

    # Common
    if d.common:
        print(f"\n┌─ PROGRAM COMMON SECTIONS")
        for sec in d.common:
            _render_section(sec)

    # Track sections
    s = d.summary["program_sections"]
    label = f"PROGRAM SECTIONS ({s['satisfied_or_in_progress']}/{s['total_codes']} codes covered)"
    if d.track:
        label = f"PROGRAM TRACK [{d.track}] ({s['satisfied_or_in_progress']}/{s['total_codes']} codes covered)"
    print(f"\n┌─ {label}")
    for sec in d.track_sections:
        _render_section(sec)


def _render_section(sec: SectionDiff) -> None:
    sec_icon = "✅" if sec.section_satisfied else "🔸"
    print(f"│  {sec_icon} ## {sec.header or '(no header)'}  ({sec.n_done}/{sec.n_required})")
    for c in sec.courses:
        if c.status == "info":
            note = f"{c.credits or '?'} cr"
            t = (c.title or "")[:40]
            print(f"│       · {t}  ({note})")
            continue
        icon = {"satisfied": "✅", "in_progress": "⏳", "missing": "❌", "skipped": "⏭"}[c.status]
        via = f" [{c.via}]" if c.via else ""
        or_mark = " (or)" if c.is_or_alternative else ""
        code = (c.code or "—").ljust(14)
        title = (c.title or "")[:40].ljust(40)
        cred = c.credits or ""
        print(f"│   {icon} {code} {title} {cred:>4}{via}{or_mark}")


def _slug_from_program_name(name: str) -> str:
    """Map "Computer and Data Science (BA)" → "computer-data-science-ba" """
    s = name.lower()
    s = s.replace("(", "").replace(")", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    # NYU uses "computer-data-science-ba" not "computer-and-data-science-ba"
    s = s.replace("-and-", "-")
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--slug", help="program slug (default: inferred from transcript)")
    ap.add_argument("--track", default=None)
    ap.add_argument("--skip", action="append", default=[],
                    help="mark a CAS Core category, course code, or section "
                         "header as skipped (manually fulfilled). Repeatable.")
    ap.add_argument("--json", help="dump diff to JSON file")
    args = ap.parse_args()

    parse = parse_transcript(args.pdf)
    state = build_state_from_parse(parse)

    slug = args.slug
    if not slug:
        if not parse.current_program or not parse.current_program.majors:
            print("[err] couldn't infer program from transcript; pass --slug",
                  file=sys.stderr)
            return 2
        major_name = parse.current_program.majors[0]
        degree_token = "ba" if (parse.current_program.degree or "").lower().startswith(
            "bachelor of arts") else "bs"
        slug = _slug_from_program_name(major_name + " " + degree_token)
        print(f"[info] inferred slug: {slug}")

    program, core = load_from_mongo(slug, args.track)
    merged = merge(program, core)
    diff = compute_diff(state, merged, skips=args.skip)
    render(diff)

    if args.json:
        with open(args.json, "w") as f:
            json.dump(asdict(diff), f, indent=2, default=str)
        print(f"\n[info] dumped → {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
