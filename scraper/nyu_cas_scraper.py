#!/usr/bin/env python3
"""
NYU CAS Course + Professor Scraper
====================================
Pulls every (course, section, professor) tuple for NYU's College of Arts and
Science from the public bulletins.nyu.edu Class Search API. No login or
API key required.

Usage:
    python nyu_cas_scraper.py                    # default = Summer 2026 (1266)
    python nyu_cas_scraper.py --term 1264        # Spring 2026
    python nyu_cas_scraper.py --include-gsas     # also include grad CAS (GSAS, -GA)
    python nyu_cas_scraper.py --output mine.csv

Term codes:
    1268 = Fall 2026 (when available)
    1266 = Summer 2026
    1264 = Spring 2026
    1262 = January 2026
    1258 = Fall 2025
    1256 = Summer 2025
    1254 = Spring 2025
    (pattern: 12XY where +2 each consecutive session)

Output: a CSV with one row per section, including instructor.
Filter by professor afterwards with grep / pandas / Excel:
    grep -i "Cho" cas_courses.csv
"""

from __future__ import annotations
import argparse
import csv
import json
import sys
import time
from typing import List, Dict
import urllib.request
import urllib.error


API_URL = "https://bulletins.nyu.edu/class-search/api/?page=fose&route=search"

# ─── CAS subject prefixes (extracted from bulletins.nyu.edu/class-search/) ───
# Undergrad CAS = -UA, Noncredit CAS = -NA
CAS_UNDERGRAD = [
    "ANST-UA", "ANTH-UA", "ARTH-UA", "BIOL-UA", "CAMS-UA", "CHEM-UA",
    "CLASS-UA", "COHRT-UA", "COLIT-UA", "CORE-UA", "CRWRI-UA", "CSCI-UA",
    "DRLIT-UA", "DS-UA", "EAST-UA", "ENGL-UA", "ENVST-UA", "EURO-UA",
    "EXPOS-UA", "FREN-UA", "FYSEM-UA", "GERM-UA", "HBRJD-UA", "HEL-UA",
    "HIST-UA", "INTRL-UA", "IRISH-UA", "ITAL-UA", "JOUR-UA", "LATC-UA",
    "LING-UA", "LWSOC-UA", "MATH-UA", "MEDI-UA", "MEIS-UA", "MUSIC-UA",
    "NEURL-UA", "NODEP-UA", "PHIL-UA", "PHYS-UA", "POL-UA", "PORT-UA",
    "PSYCH-UA", "PUBPL-UA", "RELST-UA", "RUSSN-UA", "SCA-UA", "SCHOL-UA",
    "SOC-UA", "SPAN-UA",
]
CAS_NONCREDIT = ["DEU-NA", "GSTM-NA", "RSCH-NA"]

# GSAS (grad CAS) — optional
GSAS = [
    "AFRS-GA", "AMST-GA", "ANST-GA", "ANTH-GA", "ARTH-GA", "BIOE-GA",
    "BIOL-GA", "BMIN-GA", "BMSC-GA", "CEH-GA", "CHEM-GA", "CLASS-GA",
    "COLIT-GA", "CRWRI-GA", "CSCI-GA", "DS-GA", "EAST-GA", "EHSC-GA",
    "ENGL-GA", "EURO-GA", "FINH-GA", "FREN-GA", "GERM-GA", "GSAS-GA",
    "HBRJD-GA", "HEL-GA", "HIST-GA", "IFST-GA", "INTRL-GA", "IRISH-GA",
    "ISAW-GA", "ITAL-GA", "JOUR-GA", "LATC-GA", "LING-GA", "MATH-GA",
    "MEDI-GA", "MEIS-GA", "MSMS-GA", "MUSIC-GA", "NEST-GA", "NEURL-GA",
    "PDPSA-GA", "PHIL-GA", "PHYS-GA", "POL-GA", "PORT-GA", "PSYCH-GA",
    "PUBHM-GA", "RELST-GA", "RUSSN-GA", "SOC-GA", "SPAN-GA",
]


# ─── Banner FOSE schedule code → human label (kept short) ───────────────────
SCHED_MAP = {
    "LEC": "Lecture", "RCT": "Recitation", "LAB": "Lab", "SEM": "Seminar",
    "IND": "Independent", "CLI": "Clinic", "STU": "Studio", "WSP": "Workshop",
    "FLD": "Field", "RES": "Research", "INT": "Internship",
}
STAT_MAP = {"A": "Open", "C": "Closed", "W": "Waitlist", "X": "Cancelled"}


def post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    """Make a POST request with a JSON body and return parsed JSON."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (CASCourseScraper/1.0)",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_subject(subject: str, term_code: str) -> List[Dict]:
    """
    Fetch all sections for a subject prefix (e.g. "CSCI-UA") in given term.
    Tries 'subject' criteria first; falls back to 'keyword' if API rejects.
    """
    payload = {
        "other": {"srcdb": term_code},
        "criteria": [{"field": "subject", "value": subject}],
    }
    try:
        data = post_json(API_URL, payload)
    except urllib.error.HTTPError as e:
        print(f"  ! HTTP {e.code} on subject={subject}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  ! Net error on subject={subject}: {e}", file=sys.stderr)
        return []

    # Fallback: NYU's API may use "keyword" instead of "subject"
    if data.get("fatal") or "results" not in data:
        payload["criteria"] = [{"field": "keyword", "value": subject}]
        try:
            data = post_json(API_URL, payload)
        except Exception as e:
            print(f"  ! Fallback failed on {subject}: {e}", file=sys.stderr)
            return []

    if data.get("fatal"):
        print(f"  ! API fatal on {subject}: {data.get('fatal')}",
              file=sys.stderr)
        return []

    results = data.get("results", [])
    count = data.get("count", len(results))
    if count > len(results):
        print(f"  ! {subject}: API says count={count} but only got "
              f"{len(results)} (pagination may be needed)", file=sys.stderr)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape NYU CAS courses + professors from the public "
                    "bulletins.nyu.edu API.")
    parser.add_argument("--term", default="1266",
                        help="Term code (default 1266 = Summer 2026). "
                             "Try 1264 for Spring 2026, 1268 for Fall 2026.")
    parser.add_argument("--output", default="cas_courses.csv",
                        help="Output CSV path (default: cas_courses.csv)")
    parser.add_argument("--include-gsas", action="store_true",
                        help="Also include GSAS (grad CAS, -GA) subjects.")
    parser.add_argument("--delay", type=float, default=0.4,
                        help="Seconds between requests (default 0.4)")
    parser.add_argument("--json-output", default=None,
                        help="Optional path to also dump raw JSON.")
    args = parser.parse_args()

    subjects = CAS_UNDERGRAD + CAS_NONCREDIT
    if args.include_gsas:
        subjects = subjects + GSAS

    print(f"Fetching {len(subjects)} CAS subjects for term {args.term}…\n")
    rows: List[Dict] = []
    raw: Dict[str, List[Dict]] = {}
    seen = set()

    for i, subj in enumerate(subjects, 1):
        results = fetch_subject(subj, args.term)
        raw[subj] = results
        n_added = 0
        for r in results:
            code = (r.get("code") or "").strip()
            section = (r.get("no") or "").strip()
            key = (code, section)
            if not code or key in seen:
                continue
            seen.add(key)
            instructor = (r.get("instr") or "").strip() or "Staff"
            rows.append({
                "subject_prefix": subj,
                "course_code": code,
                "course_name": (r.get("name") or "").strip(),
                "section": section,
                "crn": (r.get("crn") or "").strip(),
                "instructor": instructor,
                "schedule": (r.get("meets") or "").strip(),
                "type": SCHED_MAP.get(r.get("schd", ""), r.get("schd", "")),
                "status": STAT_MAP.get(r.get("stat", ""), r.get("stat", "")),
                "credits": (r.get("total") or "").strip(),
            })
            n_added += 1
        print(f"  [{i:3d}/{len(subjects)}] {subj:<12s} → "
              f"{len(results):4d} sections ({n_added} new)")
        time.sleep(args.delay)

    if not rows:
        print("\n! No data fetched. Common causes:", file=sys.stderr)
        print("  - Term has no published schedule yet", file=sys.stderr)
        print("  - Network/firewall blocking bulletins.nyu.edu",
              file=sys.stderr)
        print("  - API field names changed (try --include-gsas to confirm)",
              file=sys.stderr)
        sys.exit(1)

    # Sort: by course_code then section
    rows.sort(key=lambda r: (r["course_code"], r["section"]))

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)

    # Summary
    courses = {r["course_code"] for r in rows}
    instr_set = {r["instructor"] for r in rows if r["instructor"] != "Staff"}
    by_instr: Dict[str, int] = {}
    for r in rows:
        by_instr[r["instructor"]] = by_instr.get(r["instructor"], 0) + 1
    top = sorted(by_instr.items(), key=lambda x: -x[1])[:5]

    print(f"\n✓ Wrote {len(rows)} sections to {args.output}")
    print(f"  Unique courses     : {len(courses)}")
    print(f"  Unique instructors : {len(instr_set)}")
    print(f"  Top instructors by section count:")
    for name, n in top:
        print(f"    {n:3d} × {name}")
    print(f"\nTo find a specific professor:")
    print(f"  grep -i \"<name>\" {args.output}")
    print(f"  # or in Python:  pandas.read_csv('{args.output}')"
          ".query('instructor.str.contains(\"Cho\", case=False)')")


if __name__ == "__main__":
    main()