"""
forecasting.py
---------------
Weight trend forecasting using scikit-learn Linear Regression.

Why linear regression and not ARIMA/Prophet:
- Dataset size for a personal tracker is small (weeks-months of data).
- A linear trend is interpretable ("losing ~0.3kg/week") which matters
  more here than marginal accuracy gains from a heavier time-series model.
- Zero extra dependencies beyond what's already in the stack.
"""

from datetime import timedelta
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

MIN_POINTS_FOR_FORECAST = 3  # below this, a "trend" is statistically meaningless


def _prepare_xy(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, pd.Timestamp]:
    """Convert dates to ordinal day-offsets for regression input."""
    base_date = df["date"].min()
    x = (df["date"] - base_date).dt.days.values.reshape(-1, 1)
    y = df["weight_kg"].values
    return x, y, base_date


def forecast_weight(df: pd.DataFrame, days_ahead: int = 30) -> Optional[pd.DataFrame]:
    """
    Fit a linear model on historical weight data and project forward.

    Returns None if there isn't enough data to fit a meaningful trend
    (caller is responsible for showing an appropriate UI message).
    """
    if df.empty or len(df) < MIN_POINTS_FOR_FORECAST:
        return None

    x, y, base_date = _prepare_xy(df)

    model = LinearRegression()
    model.fit(x, y)

    last_offset = int(x.max())
    future_offsets = np.arange(last_offset + 1, last_offset + days_ahead + 1).reshape(-1, 1)
    predictions = model.predict(future_offsets)

    future_dates = [base_date + timedelta(days=int(o)) for o in future_offsets.flatten()]

    forecast_df = pd.DataFrame({
        "date": future_dates,
        "predicted_weight_kg": np.round(predictions, 2),
    })
    return forecast_df


def get_trend_slope_per_week(df: pd.DataFrame) -> Optional[float]:
    """Returns kg/week trend — positive = gaining, negative = losing."""
    if df.empty or len(df) < MIN_POINTS_FOR_FORECAST:
        return None
    x, y, _ = _prepare_xy(df)
    model = LinearRegression().fit(x, y)
    slope_per_day = model.coef_[0]
    return round(slope_per_day * 7, 3)


def estimate_target_date(df: pd.DataFrame, target_weight: float) -> Optional[pd.Timestamp]:
    """
    Estimate the calendar date at which the linear trend crosses the
    target weight. Returns None if:
    - not enough data,
    - the trend is flat (slope ~0, would never reach target),
    - the trend is moving away from the target.
    """
    if df.empty or len(df) < MIN_POINTS_FOR_FORECAST:
        return None

    x, y, base_date = _prepare_xy(df)
    model = LinearRegression().fit(x, y)
    slope = model.coef_[0]
    intercept = model.intercept_

    if abs(slope) < 1e-6:
        return None  # flat trend, target unreachable on current trajectory

    # Solve target_weight = slope * day + intercept  ->  day = (target - intercept) / slope
    target_day_offset = (target_weight - intercept) / slope
    current_day_offset = int(x.max())

    if target_day_offset < current_day_offset:
        return None  # target is in the "past" relative to trend -> wrong direction

    target_date = base_date + timedelta(days=float(target_day_offset))
    return target_date
