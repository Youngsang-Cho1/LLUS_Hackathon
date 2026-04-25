"""
Hard-coded equivalency tables.

These are best-effort starting points. NYU's official transfer evaluation
lives in Albert and is per-student; treat these as DEFAULTS that the user
should be able to override.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# AP Test Credit → CAS course equivalents
# Source: NYU CAS AP credit policy (https://cas.nyu.edu/), as of 2024-2025
# Each AP subject can satisfy up to N credits; we mark the specific CAS
# course codes it counts toward when applicable.
# ---------------------------------------------------------------------------
#
# Format:  AP subject (case-insensitive substring match) →
#          list of equivalent CAS course codes that get marked "satisfied"
#
# Notes:
# - "Calculus BC" (score 4-5) typically grants credit for both Calc I and II
# - "Calculus AB" (score 4-5) grants Calc I only
# - "Chemistry" (score 4-5) grants General Chem I + II + labs
# - Some APs satisfy a *core* category but not a specific course code; we
#   list them under `core_category_satisfied` instead.

AP_TO_COURSE: dict[str, list[str]] = {
    "Calculus BC":          ["MATH-UA 121", "MATH-UA 122"],
    "Calculus AB":          ["MATH-UA 121"],
    "Chemistry":            ["CHEM-UA 125", "CHEM-UA 126"],
    "Biology":              ["BIOL-UA 11"],
    "Physics C: Mechanics": ["PHYS-UA 91"],
    "Physics C Elec & Magnetism": ["PHYS-UA 93"],
    "Physics 1":            [],   # general elective only
    "Physics 2":            [],
    "Statistics":           ["MATH-UA 103"],   # counts as elementary stats
    "Computer Science A":   [],   # CAS doesn't grant CSCI-UA equivalent
    "Economics - Macroeconomics": ["ECON-UA 1"],
    "Economics - Microeconomics": ["ECON-UA 2"],
    "Psychology":           ["PSYCH-UA 1"],
    "English Literature":   [],
    "English Language":     [],
}

# AP subjects that satisfy a CAS Core category (Foundations of Scientific
# Inquiry / Foundations of Contemporary Culture)
AP_TO_CORE_CATEGORY: dict[str, list[str]] = {
    "Calculus BC":          ["Quantitative Reasoning"],
    "Calculus AB":          ["Quantitative Reasoning"],
    "Statistics":           ["Quantitative Reasoning"],
    "Chemistry":            ["Physical Science"],
    "Physics C: Mechanics": ["Physical Science"],
    "Physics C Elec & Magnetism": ["Physical Science"],
    "Physics 1":            ["Physical Science"],
    "Physics 2":            ["Physical Science"],
    "Biology":              ["Life Science"],
    "Psychology":           ["Societies and the Social Sciences"],
}


# ---------------------------------------------------------------------------
# Tandon → CAS course equivalents
# Used when a student transfers from Tandon (CS-UY, MA-UY, EG-UY, etc.) to
# CAS. These are *plausible* mappings — the registrar makes the final call.
# ---------------------------------------------------------------------------

# Compound equivalents: student must have ALL keys to earn the value.
# (e.g., NYU CAS treats the EXPOS-UA 4 + EXPOS-UA 9 international writing
# sequence as equivalent to EXPOS-UA 1 Writing the Essay.)
COMPOUND_EQUIVALENTS: list[tuple[list[str], str]] = [
    (["EXPOS-UA 4", "EXPOS-UA 9"], "EXPOS-UA 1"),
]


TANDON_TO_CAS: dict[str, list[str]] = {
    # CS-UY → CSCI-UA
    "CS-UY 1114":  ["CSCI-UA 101"],   # Intro to Programming & Problem Solving ≈ Intro to CS
    "CS-UY 1133":  ["CSCI-UA 2"],     # Engineering Programming
    "CS-UY 1134":  ["CSCI-UA 102"],   # Data Structures
    "CS-UY 2124":  ["CSCI-UA 102"],   # OO programming
    "CS-UY 2214":  ["CSCI-UA 201"],   # Computer Architecture
    "CS-UY 2413":  ["CSCI-UA 102"],   # Data Structures & Algorithms
    "CS-UY 3113":  ["CSCI-UA 480"],   # OS or related
    # Math
    "MA-UY 1024":  ["MATH-UA 121"],   # Calc I
    "MA-UY 1124":  ["MATH-UA 122"],   # Calc II
    "MA-UY 2114":  ["MATH-UA 123"],   # Calc III
    "MA-UY 2034":  ["MATH-UA 140"],   # Linear Algebra (also covers Diff Eq partially)
    "MA-UY 2224":  ["MATH-UA 235"],   # Probability and Statistics
    "MA-UY 3054":  ["MATH-UA 240"],   # Combinatorics
    # Writing — same EXPOS-UA codes already
    # Physics
    "PH-UY 1013":  ["PHYS-UA 91"],
    "PH-UY 2023":  ["PHYS-UA 93"],
}
