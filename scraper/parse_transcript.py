"""
NYU Albert transcript PDF parser.

Extracts: student info, program(s) per term, completed courses, in-progress
courses, AP test credits, and the most recent (current) program.

Usage:
    python parse_transcript.py path/to/transcript.pdf
    python parse_transcript.py path/to/transcript.pdf --json /tmp/student.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pdfplumber

# e.g. "CS-UY 1114 4.0 B+", "CSCI-UA 201 4.0 B", "EXPOS-UA 4 4.0 B+", "TECH-UB 26 1.5 ***"
COURSE_RE = re.compile(
    r"(?P<code>[A-Z]{2,5}-[A-Z]{2})\s+"
    r"(?P<num>\d+[A-Z]?)\s+"
    r"(?P<credits>\d+\.\d+)\s+"
    r"(?P<grade>\*\*\*|[A-Z][+\-]?|P|F|W|I)(?=\s|$)"
)
TERM_RE = re.compile(
    r"^(Fall|Spring|Summer|Winter|January|May|September)\s+\d{4}$"
)
AP_RE = re.compile(r"^ADV_PL\s+(?P<subject>.+?)\s+(?P<units>\d+\.\d+)$")


@dataclass
class Course:
    code: str
    title: str
    credits: float
    grade: str
    term: str | None
    school: str | None
    degree: str | None
    majors: list[str] = field(default_factory=list)
    minors: list[str] = field(default_factory=list)


@dataclass
class APCredit:
    subject: str
    units: float


@dataclass
class TermProgram:
    term: str
    school: str | None
    degree: str | None
    majors: list[str]
    minors: list[str]


@dataclass
class TranscriptParse:
    student_name: str | None
    student_id: str | None
    print_date: str | None
    current_program: TermProgram | None
    term_programs: list[TermProgram]
    completed_courses: list[Course]
    in_progress_courses: list[Course]
    ap_credits: list[APCredit]


def extract_text(pdf_path: Path) -> str:
    """NYU transcripts use a 2-column layout. Extract each column separately
    and concatenate (left column first, then right column), so course rows
    don't get jumbled across columns."""
    chunks: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            chunks.append(_extract_two_columns(page))
    return "\n".join(chunks)


def _extract_two_columns(page) -> str:
    # Filter out the giant "COPY" watermark (48pt Calibri-BoldItalic) which
    # bleeds individual characters into the body text and breaks word grouping.
    body_chars = [c for c in page.chars if c.get("size", 0) < 20]
    filtered = page.filter(lambda obj: obj.get("size", 0) < 20 if "size" in obj else True)

    mid = page.width / 2
    words = filtered.extract_words(use_text_flow=False, keep_blank_chars=False)

    left = [w for w in words if (w["x0"] + w["x1"]) / 2 < mid]
    right = [w for w in words if (w["x0"] + w["x1"]) / 2 >= mid]

    return _words_to_lines(left) + "\n" + _words_to_lines(right)


def _words_to_lines(words: list[dict], y_tol: float = 3.0) -> str:
    """Group words into lines by y-coordinate, then join in reading order."""
    if not words:
        return ""
    words = sorted(words, key=lambda w: (round(w["top"] / y_tol), w["x0"]))
    lines: list[list[dict]] = []
    cur_top: float | None = None
    cur_line: list[dict] = []
    for w in words:
        if cur_top is None or abs(w["top"] - cur_top) <= y_tol:
            cur_line.append(w)
            cur_top = w["top"] if cur_top is None else cur_top
        else:
            lines.append(cur_line)
            cur_line = [w]
            cur_top = w["top"]
    if cur_line:
        lines.append(cur_line)
    return "\n".join(" ".join(w["text"] for w in line) for line in lines)


def _extract_meta(lines: list[str]) -> tuple[str | None, str | None, str | None]:
    name = sid = pdate = None
    for l in lines:
        if l.startswith("Name:"):
            name = l[len("Name:"):].strip()
        elif l.startswith("Student ID:"):
            sid = l.split(":", 1)[1].strip()
        elif l.startswith("Print Date:"):
            pdate = l.split(":", 1)[1].strip()
    return name, sid, pdate


def _extract_ap(lines: list[str]) -> list[APCredit]:
    ap = []
    for l in lines:
        m = AP_RE.match(l)
        if m:
            ap.append(APCredit(subject=m.group("subject").strip(),
                                units=float(m.group("units"))))
    return ap


def parse_transcript(pdf_path: Path) -> TranscriptParse:
    text = extract_text(pdf_path)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    name, sid, pdate = _extract_meta(lines)
    ap = _extract_ap(lines)

    completed: list[Course] = []
    in_progress: list[Course] = []
    term_programs: list[TermProgram] = []
    last_course: Course | None = None

    state = "pre"
    cur_term: str | None = None
    cur_school: str | None = None
    cur_degree: str | None = None
    cur_majors: list[str] = []
    cur_minors: list[str] = []
    title_buffer: list[str] = []

    def flush_term_program():
        if cur_term and (cur_school or cur_majors or cur_minors):
            term_programs.append(TermProgram(
                term=cur_term, school=cur_school, degree=cur_degree,
                majors=list(cur_majors), minors=list(cur_minors),
            ))

    for line in lines:
        # Term boundary
        if TERM_RE.match(line):
            flush_term_program()
            cur_term = line
            cur_school = None
            cur_degree = None
            cur_majors = []
            cur_minors = []
            title_buffer = []
            state = "term_meta"
            continue

        # End of term courses → totals block
        if line.startswith("AHRS") or line.startswith("Current ") or line.startswith("Cumulative "):
            title_buffer = []
            state = "totals"
            continue

        if state in ("pre", "totals"):
            continue

        # In-term metadata lines
        if "School of" in line or "College of" in line:
            cur_school = line
            continue
        if line.startswith("Bachelor") or line.startswith("Master") or line.startswith("Doctor"):
            cur_degree = line
            continue
        if line.startswith("Major:"):
            cur_majors.append(line.split(":", 1)[1].strip())
            continue
        if line.startswith("Minor:"):
            cur_minors.append(line.split(":", 1)[1].strip())
            continue
        if line.startswith("Term Honor:") or line.startswith("Leave of Absence") or line.startswith("Return from Leave"):
            continue

        # Course line?
        m = COURSE_RE.search(line)
        if m:
            code = f"{m.group('code')} {m.group('num')}"
            credits_val = float(m.group("credits"))
            grade = m.group("grade")

            prefix = line[: m.start()].rstrip()
            if prefix:
                # New course's title is on the same line. If buffer has content,
                # it's a wrapped tail of the PREVIOUS course's title.
                if title_buffer and last_course is not None:
                    last_course.title = (last_course.title + " " + " ".join(title_buffer)).strip()
                title = prefix
            else:
                title = " ".join(title_buffer).strip()
            title_buffer = []

            course = Course(
                code=code, title=title, credits=credits_val, grade=grade,
                term=cur_term, school=cur_school, degree=cur_degree,
                majors=list(cur_majors), minors=list(cur_minors),
            )
            (in_progress if grade == "***" else completed).append(course)
            last_course = course
            state = "courses"
            continue

        # Otherwise this line is a wrapped title fragment
        title_buffer.append(line)

    flush_term_program()

    current_program = term_programs[-1] if term_programs else None

    return TranscriptParse(
        student_name=name, student_id=sid, print_date=pdate,
        current_program=current_program,
        term_programs=term_programs,
        completed_courses=completed,
        in_progress_courses=in_progress,
        ap_credits=ap,
    )


def render_summary(t: TranscriptParse) -> None:
    print(f"Student: {t.student_name}  ({t.student_id})  printed {t.print_date}")
    if t.current_program:
        cp = t.current_program
        print(f"Current program: {cp.school} — {cp.degree}")
        if cp.majors: print(f"  Major(s): {', '.join(cp.majors)}")
        if cp.minors: print(f"  Minor(s): {', '.join(cp.minors)}")

    print(f"\nAP credits ({sum(a.units for a in t.ap_credits):.0f} total):")
    for a in t.ap_credits:
        print(f"  • {a.subject} — {a.units}")

    print(f"\nCompleted courses ({len(t.completed_courses)}):")
    for c in t.completed_courses:
        print(f"  [{c.term:<13}] {c.code:<14} {c.title[:45]:<45} {c.credits:>4} {c.grade}")

    print(f"\nIn-progress courses ({len(t.in_progress_courses)}):")
    for c in t.in_progress_courses:
        print(f"  [{c.term:<13}] {c.code:<14} {c.title[:45]:<45} {c.credits:>4}")


def main() -> int:
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("pdf", type=Path)
    ap_.add_argument("--json", help="dump structured result to JSON file")
    args = ap_.parse_args()

    if not args.pdf.exists():
        print(f"[err] file not found: {args.pdf}", file=sys.stderr)
        return 2

    result = parse_transcript(args.pdf)
    render_summary(result)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)
        print(f"\n[info] dumped JSON → {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
