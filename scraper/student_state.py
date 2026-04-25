"""
Build a normalized "student state" from a parsed transcript.

A StudentState collects everything we know a student has already covered:
  - completed_codes:    course codes with passing grades
  - in_progress_codes:  course codes currently enrolled (***)
  - satisfied_by_ap:    course codes satisfied via AP credit equivalents
  - satisfied_by_transfer: course codes satisfied via Tandon→CAS or other transfer
  - core_categories_satisfied: CAS core categories already met (e.g. via AP)
  - all_satisfied_codes: union of everything above

Usage:
    from student_state import build_state_from_parse
    parse = parse_transcript("...")
    state = build_state_from_parse(parse)
    state.has("CSCI-UA 101")          # bool
    state.satisfies_core("Quantitative Reasoning")
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable

from credit_mappings import (
    AP_TO_CORE_CATEGORY, AP_TO_COURSE, COMPOUND_EQUIVALENTS, TANDON_TO_CAS,
)

# Grades that count as "passed" (not in-progress, not failed/withdrawn)
PASSING_GRADES = {
    "A+", "A", "A-",
    "B+", "B", "B-",
    "C+", "C", "C-",
    "D+", "D", "D-",
    "P",   # pass (NYU credit/no-credit)
}
IN_PROGRESS_GRADES = {"***"}


@dataclass
class StudentState:
    completed_codes: set[str]
    in_progress_codes: set[str]
    satisfied_by_ap: set[str]
    satisfied_by_transfer: set[str]
    core_categories_satisfied: set[str]
    notes: list[str] = field(default_factory=list)

    @property
    def all_satisfied_codes(self) -> set[str]:
        """Codes that count as 'done' for requirement matching purposes."""
        return (self.completed_codes | self.in_progress_codes
                | self.satisfied_by_ap | self.satisfied_by_transfer)

    def has(self, code: str) -> bool:
        return code in self.all_satisfied_codes

    def satisfies_core(self, category: str) -> bool:
        return category in self.core_categories_satisfied

    def to_dict(self) -> dict:
        d = asdict(self)
        # JSON-friendly: sets → sorted lists
        for k, v in d.items():
            if isinstance(v, set):
                d[k] = sorted(v)
        d["completed_codes"] = sorted(self.completed_codes)
        d["in_progress_codes"] = sorted(self.in_progress_codes)
        d["satisfied_by_ap"] = sorted(self.satisfied_by_ap)
        d["satisfied_by_transfer"] = sorted(self.satisfied_by_transfer)
        d["core_categories_satisfied"] = sorted(self.core_categories_satisfied)
        d["all_satisfied_codes"] = sorted(self.all_satisfied_codes)
        return d


def _is_tandon(code: str) -> bool:
    """Tandon course codes use -UY suffix."""
    return "-UY" in code


def _ap_match(subject: str, mapping: dict[str, list[str]]) -> list[str]:
    """Case-insensitive substring lookup for AP subject names."""
    subj_lower = subject.lower()
    for key, vals in mapping.items():
        if key.lower() in subj_lower or subj_lower in key.lower():
            return vals
    return []


def build_state_from_parse(parse) -> StudentState:
    """
    `parse` is a TranscriptParse from parse_transcript.py
    (or an equivalent dict).
    """
    # Allow dict input (from JSON) too
    if isinstance(parse, dict):
        completed = parse.get("completed_courses", [])
        in_progress = parse.get("in_progress_courses", [])
        ap_credits = parse.get("ap_credits", [])
    else:
        completed = parse.completed_courses
        in_progress = parse.in_progress_courses
        ap_credits = parse.ap_credits

    notes: list[str] = []

    completed_codes: set[str] = set()
    in_progress_codes: set[str] = set()
    satisfied_by_transfer: set[str] = set()

    def _course_code(c) -> str:
        return c["code"] if isinstance(c, dict) else c.code

    def _course_grade(c) -> str:
        return c["grade"] if isinstance(c, dict) else c.grade

    for c in completed:
        code = _course_code(c)
        grade = _course_grade(c)
        if grade in PASSING_GRADES:
            completed_codes.add(code)
            # If it's a Tandon course, also mark its CAS equivalent satisfied
            if _is_tandon(code) and code in TANDON_TO_CAS:
                for eq in TANDON_TO_CAS[code]:
                    satisfied_by_transfer.add(eq)
                    notes.append(f"transfer: {code} → {eq}")

    for c in in_progress:
        code = _course_code(c)
        in_progress_codes.add(code)
        if _is_tandon(code) and code in TANDON_TO_CAS:
            for eq in TANDON_TO_CAS[code]:
                satisfied_by_transfer.add(eq)
                notes.append(f"transfer (in-progress): {code} → {eq}")

    # AP credit mapping (deduplicated — same AP subject taken twice grants
    # one set of equivalents, not multiple)
    satisfied_by_ap: set[str] = set()
    core_categories_satisfied: set[str] = set()
    seen_ap: set[str] = set()
    for ap in ap_credits:
        subject = ap["subject"] if isinstance(ap, dict) else ap.subject
        if subject in seen_ap:
            continue
        seen_ap.add(subject)

        course_eqs = _ap_match(subject, AP_TO_COURSE)
        for eq in course_eqs:
            satisfied_by_ap.add(eq)
            notes.append(f"AP {subject} → {eq}")

        cat_eqs = _ap_match(subject, AP_TO_CORE_CATEGORY)
        for cat in cat_eqs:
            core_categories_satisfied.add(cat)
            notes.append(f"AP {subject} → core: {cat}")

    # Compound equivalents (e.g. EXPOS-UA 4 + 9 → EXPOS-UA 1)
    all_codes = completed_codes | in_progress_codes
    for required, granted in COMPOUND_EQUIVALENTS:
        if all(r in all_codes for r in required):
            satisfied_by_transfer.add(granted)
            notes.append(f"compound: {' + '.join(required)} → {granted}")

    return StudentState(
        completed_codes=completed_codes,
        in_progress_codes=in_progress_codes,
        satisfied_by_ap=satisfied_by_ap,
        satisfied_by_transfer=satisfied_by_transfer,
        core_categories_satisfied=core_categories_satisfied,
        notes=notes,
    )


def render_state(s: StudentState) -> None:
    print(f"Completed: {len(s.completed_codes)} courses")
    for c in sorted(s.completed_codes): print(f"  ✓ {c}")
    print(f"\nIn-progress: {len(s.in_progress_codes)}")
    for c in sorted(s.in_progress_codes): print(f"  → {c}")
    print(f"\nSatisfied by AP: {len(s.satisfied_by_ap)}")
    for c in sorted(s.satisfied_by_ap): print(f"  AP → {c}")
    print(f"\nSatisfied by transfer (Tandon→CAS): {len(s.satisfied_by_transfer)}")
    for c in sorted(s.satisfied_by_transfer): print(f"  ⇄ {c}")
    print(f"\nCore categories satisfied: {len(s.core_categories_satisfied)}")
    for c in sorted(s.core_categories_satisfied): print(f"  ★ {c}")


if __name__ == "__main__":
    import argparse, json, sys
    from pathlib import Path
    from parse_transcript import parse_transcript

    ap_ = argparse.ArgumentParser()
    ap_.add_argument("pdf", type=Path)
    ap_.add_argument("--json", help="dump state to JSON")
    args = ap_.parse_args()

    parse = parse_transcript(args.pdf)
    state = build_state_from_parse(parse)
    render_state(state)

    if args.json:
        with open(args.json, "w") as f:
            json.dump(state.to_dict(), f, indent=2)
        print(f"\n[info] dumped → {args.json}")
