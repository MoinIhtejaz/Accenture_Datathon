"""
Filter out regrettable exits from attrition_log.csv.

Keeps only the rows where regrettable_flag is true; everything else is
dropped. The source CSV is never modified.

Usage:  python filter.py [in.csv] [out.csv]
Default: attrition_log.csv -> edited.csv
"""

import sys
from pathlib import Path

import pandas as pd

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "attrition_log.csv")
DST = Path(sys.argv[2] if len(sys.argv) > 2 else SRC.parent / "eddited_csv" / "attrition_reg.csv")

if DST.resolve() == SRC.resolve():
    sys.exit("Refusing to overwrite the source file — pick a different output path.")


def to_bool(s: pd.Series) -> pd.Series:
    """Coerce a mixed bool/str/int column to real booleans (NaN -> False)."""
    if s.dtype == bool:
        return s
    return (s.astype(str).str.strip().str.lower()
             .isin({"true", "1", "yes", "y", "t"}))


df = pd.read_csv(SRC)
mask = to_bool(df["regrettable_flag"])

filtered = df[mask].copy()

print(f"{SRC.name}: {len(df):,} rows")
print(f"  kept (regrettable):    {len(filtered):,}")
print(f"  removed:               {(~mask).sum():,}")

filtered.to_csv(DST, index=False)
print(f"Wrote {DST}")
