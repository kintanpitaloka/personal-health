"""
storage.py
----------
Handles all CSV read/write logic for the Personal Health Dashboard.

Design note:
This module is intentionally the ONLY place that touches the filesystem.
If you later migrate to Postgres/SQLite, you only need to rewrite this
file — calculations.py, forecasting.py, and charts.py stay untouched.
"""

import os
import pandas as pd
from datetime import date

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CSV_PATH = os.path.join(DATA_DIR, "health_data.csv")

# Canonical schema — every row in the CSV must have exactly these columns.
COLUMNS = [
    "date", "weight_kg", "height_cm", "age", "gender",
    "activity_level", "bmi", "bmi_category", "bmr", "tdee"
]


def ensure_data_dir_exists() -> None:
    """Create the data/ directory if it doesn't exist yet."""
    os.makedirs(DATA_DIR, exist_ok=True)


def load_data() -> pd.DataFrame:
    """
    Load historical health records.

    Handles gracefully:
    - Missing CSV file (first run) -> returns empty DataFrame with correct schema
    - Corrupt / empty CSV -> returns empty DataFrame with correct schema
    - Malformed rows -> dropped with a warning count, doesn't crash the app
    """
    ensure_data_dir_exists()

    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(columns=COLUMNS)

    try:
        df = pd.read_csv(CSV_PATH)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame(columns=COLUMNS)

    if df.empty:
        return pd.DataFrame(columns=COLUMNS)

    # Guard against schema drift (e.g. manually edited CSV missing a column)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[COLUMNS]

    # Coerce types; invalid rows become NaT/NaN and are dropped rather than
    # crashing the whole app on one bad row.
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    numeric_cols = ["weight_kg", "height_cm", "age", "bmi", "bmr", "tdee"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["date", "weight_kg", "height_cm", "age"])
    dropped = before - len(df)
    if dropped > 0:
        # Streamlit warning is raised by the caller (app.py), not here,
        # to keep this module UI-framework-agnostic.
        df.attrs["dropped_rows"] = dropped

    return df.sort_values("date").reset_index(drop=True)


def save_entry(entry: dict) -> None:
    """
    Append a single new record to the CSV.

    If an entry already exists for the same date, it is UPDATED
    (upsert) rather than duplicated — prevents accidental double
    submission from inflating the trend charts.
    """
    ensure_data_dir_exists()
    df = load_data()

    entry_df = pd.DataFrame([entry])
    entry_df["date"] = pd.to_datetime(entry_df["date"])

    if not df.empty:
        same_day_mask = df["date"].dt.date == entry_df["date"].dt.date.iloc[0]
        df = df[~same_day_mask]  # remove existing same-day entry

    df = pd.concat([df, entry_df], ignore_index=True)
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(CSV_PATH, index=False)


def get_latest_entry(df: pd.DataFrame):
    """Return the most recent row, or None if the dataset is empty."""
    if df.empty:
        return None
    return df.iloc[-1]


def get_previous_entry(df: pd.DataFrame):
    """Return the second-most-recent row, or None if not enough data."""
    if len(df) < 2:
        return None
    return df.iloc[-2]
