"""
charts.py
---------
All Plotly chart construction lives here, kept separate from app.py
so chart styling can be iterated on without touching layout/routing code.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Consistent color palette across all charts
COLORS = {
    "weight": "#6366F1",     # indigo
    "bmi": "#10B981",        # emerald
    "forecast": "#F59E0B",   # amber
    "target": "#EF4444",     # red
    "background": "rgba(0,0,0,0)",
    "grid": "#E5E7EB",
}

BASE_LAYOUT = dict(
    plot_bgcolor=COLORS["background"],
    paper_bgcolor=COLORS["background"],
    font=dict(family="Inter, sans-serif", size=13, color="#374151"),
    margin=dict(l=40, r=20, t=50, b=40),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def weight_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Line chart of weight over time with markers for each entry."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["weight_kg"],
        mode="lines+markers",
        name="Weight (kg)",
        line=dict(color=COLORS["weight"], width=3),
        marker=dict(size=7),
        hovertemplate="%{x|%b %d, %Y}<br>%{y:.1f} kg<extra></extra>",
    ))
    fig.update_layout(**BASE_LAYOUT, title="Weight Trend Over Time",
                       xaxis_title="Date", yaxis_title="Weight (kg)")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLORS["grid"])
    return fig


def bmi_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Line chart of BMI over time with WHO category reference bands."""
    fig = go.Figure()

    # Reference bands for BMI categories
    bands = [
        (0, 18.5, "rgba(59,130,246,0.08)"),    # underweight
        (18.5, 25, "rgba(16,185,129,0.08)"),   # normal
        (25, 30, "rgba(245,158,11,0.08)"),     # overweight
        (30, 45, "rgba(239,68,68,0.08)"),      # obese
    ]
    for y0, y1, color in bands:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=color, line_width=0)

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["bmi"],
        mode="lines+markers",
        name="BMI",
        line=dict(color=COLORS["bmi"], width=3),
        marker=dict(size=7),
        hovertemplate="%{x|%b %d, %Y}<br>BMI: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(**BASE_LAYOUT, title="BMI Trend Over Time",
                       xaxis_title="Date", yaxis_title="BMI")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLORS["grid"])
    return fig


def monthly_progress_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart of average weight per month — shows longer-term progress."""
    monthly = df.copy()
    monthly["month"] = monthly["date"].dt.to_period("M").astype(str)
    monthly_avg = monthly.groupby("month", as_index=False)["weight_kg"].mean()
    monthly_avg["weight_kg"] = monthly_avg["weight_kg"].round(1)

    fig = px.bar(
        monthly_avg, x="month", y="weight_kg",
        text="weight_kg",
        color_discrete_sequence=[COLORS["weight"]],
    )
    fig.update_traces(textposition="outside", hovertemplate="%{x}<br>Avg: %{y} kg<extra></extra>")
    fig.update_layout(**BASE_LAYOUT, title="Monthly Average Weight",
                       xaxis_title="Month", yaxis_title="Avg Weight (kg)")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLORS["grid"])
    return fig


def forecast_chart(history_df: pd.DataFrame, forecast_df: pd.DataFrame,
                    target_weight: float = None) -> go.Figure:
    """
    Combined chart: historical weight (solid) + 30-day forecast (dashed),
    with an optional horizontal target-weight reference line.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=history_df["date"], y=history_df["weight_kg"],
        mode="lines+markers", name="Actual Weight",
        line=dict(color=COLORS["weight"], width=3),
        marker=dict(size=6),
    ))

    if forecast_df is not None and not forecast_df.empty:
        # Connect last actual point to first forecast point for visual continuity
        bridge_x = [history_df["date"].iloc[-1]] + list(forecast_df["date"])
        bridge_y = [history_df["weight_kg"].iloc[-1]] + list(forecast_df["predicted_weight_kg"])

        fig.add_trace(go.Scatter(
            x=bridge_x, y=bridge_y,
            mode="lines", name="30-Day Forecast",
            line=dict(color=COLORS["forecast"], width=3, dash="dash"),
        ))

    if target_weight is not None:
        fig.add_hline(
            y=target_weight, line_dash="dot", line_color=COLORS["target"],
            annotation_text=f"Target: {target_weight} kg",
            annotation_position="top left",
        )

    fig.update_layout(**BASE_LAYOUT, title="Weight Forecast (Next 30 Days)",
                       xaxis_title="Date", yaxis_title="Weight (kg)")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLORS["grid"])
    return fig
