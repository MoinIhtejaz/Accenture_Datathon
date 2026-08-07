"""
NovaCorp People Analytics Challenge — Raw Data Loader
======================================================

Single source of truth for: where the four source CSVs live, what their date/ID
columns are, the observation window, and the vocabularies/thresholds the audit and
cleaning pipeline both rely on. `src/data_audit.py`, `src/clean_data.py`, and
`src/validation.py` all import from this module rather than redefining these
constants, so there is exactly one place that knows the raw schema.

This module is read-only: it never writes to `employees.csv`, `attrition_log.csv`,
`engagement.csv`, or `performance.csv`, and never should.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILES = {
    "employees": BASE_DIR / "employees.csv",
    "attrition_log": BASE_DIR / "attrition_log.csv",
    "engagement": BASE_DIR / "engagement.csv",
    "performance": BASE_DIR / "performance.csv",
}
OUTPUT_TABLES_DIR = BASE_DIR / "outputs" / "tables"
OUTPUT_REPORTS_DIR = BASE_DIR / "outputs" / "reports"
OUTPUT_LOGS_DIR = BASE_DIR / "outputs" / "logs"
CLEAN_DATA_DIR = BASE_DIR / "data_clean"

# ---------------------------------------------------------------------------
# Schema: which columns are dates / string IDs, per file
# ---------------------------------------------------------------------------

DATE_COLUMNS = {
    "employees": ["hire_date", "exit_date"],
    "attrition_log": ["exit_date"],
    "engagement": ["survey_date"],
    "performance": ["review_date"],
}

STRING_ID_COLUMNS = {
    "employees": ["employee_id", "manager_id"],
    "attrition_log": ["employee_id", "manager_id_at_exit"],
    "engagement": ["employee_id"],
    "performance": ["employee_id", "reviewer_id"],
}

# ---------------------------------------------------------------------------
# Business constants shared by the audit and the cleaning pipeline
# ---------------------------------------------------------------------------

WINDOW_START = pd.Timestamp("2024-01-01")
WINDOW_END = pd.Timestamp("2025-12-31")

ENGAGEMENT_DIMENSIONS = [
    "manager_effectiveness", "psychological_safety", "recognition",
    "career_development", "senior_leadership_trust", "purpose_meaning",
    "wellbeing", "confidence_in_role_future",
]

# Nominal half-year windows used to test whether a performance review's *date* is
# consistent with its *review_cycle label*. A grace period after each window
# absorbs legitimately late-filed reviews without flagging them (see
# outputs/reports/data_quality_report.md Section 12 and docs/decision_log.md
# DEC-002 for why this exists and why the label itself is never corrected).
CYCLE_WINDOWS = {
    "2024-H1": (pd.Timestamp("2024-01-01"), pd.Timestamp("2024-06-30")),
    "2024-H2": (pd.Timestamp("2024-07-01"), pd.Timestamp("2024-12-31")),
    "2025-H1": (pd.Timestamp("2025-01-01"), pd.Timestamp("2025-06-30")),
}
CYCLE_GRACE_DAYS = 60

EXPECTED_CATEGORIES = {
    "employees": {
        "status": {"active", "departed"},
        "department": {
            "Retail Banking", "Technology", "Risk & Compliance", "Insurance",
            "Wealth Management", "Corporate Operations", "Executive Leadership",
        },
        "role_family": {
            "Operations-Processing", "Technology", "Client-Advisory",
            "Risk-Compliance", "Corporate-Support", "Executive", "Management",
        },
        "gender": {"Female", "Male", "Non-binary", "Prefer not to say"},
        "contract_type": {"Full-time", "Part-time", "Fixed-term", "Casual"},
        "hire_source": {"agency", "direct", "referral", "graduate", "acquisition"},
        "legacy_entity_code": {"Entity_A", "Entity_B", "Entity_C", "NovaCorp-Origin"},
    },
    "attrition_log": {
        "exit_type": {"voluntary", "involuntary"},
        "performance_band_at_exit": {
            "Outstanding", "High Performer", "Meets Expectations",
            "Below Expectations", "Unsatisfactory",
        },
        "pathway": {"push", "pull"},
    },
    "performance": {
        "performance_rating": {
            "Outstanding", "High Performer", "Meets Expectations",
            "Below Expectations", "Unsatisfactory",
        },
        "review_cycle": {"2024-H1", "2024-H2", "2025-H1"},
    },
}

# Plausibility bands used for screening only (no official NovaCorp band table was
# supplied — see docs/decision_log.md DEC-007). Never used to silently exclude.
COMPA_RATIO_PLAUSIBLE_RANGE = (0.3, 2.5)
ENGAGEMENT_SCALE_RANGE = (1, 5)
GOAL_ACHIEVEMENT_RANGE = (0, 100)
ROLE_LEVEL_RANGE = (1, 8)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_raw_datasets(parse_dates: bool = True) -> dict[str, pd.DataFrame]:
    """Load all four source CSVs. Read-only — never writes back to these paths.

    parse_dates=True (default): date columns are parsed at load time (used by
    src/data_audit.py, and anywhere that just needs typed dates without caring
    how the parse happened).

    parse_dates=False: date columns are left as raw strings. Used by
    src/clean_data.py, which performs and logs its own explicit parsing step
    (counting any values that fail to parse) rather than parsing silently
    inside the loader.
    """
    dfs = {}
    for name, path in DATA_FILES.items():
        dtype = {col: "string" for col in STRING_ID_COLUMNS[name]}
        kwargs = {"dtype": dtype}
        if parse_dates:
            kwargs["parse_dates"] = DATE_COLUMNS[name]
        dfs[name] = pd.read_csv(path, **kwargs)
    return dfs


def load_raw_strings() -> dict[str, pd.DataFrame]:
    """Convenience wrapper: load_raw_datasets(parse_dates=False)."""
    return load_raw_datasets(parse_dates=False)
