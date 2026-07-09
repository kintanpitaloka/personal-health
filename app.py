"""
Personal Health Dashboard
--------------------------
A portfolio-grade Streamlit analytics app for tracking weight, BMI,
and calorie needs over time, with linear-regression-based forecasting.

Run locally:
    streamlit run app.py
"""

from datetime import date

import streamlit as st

from utils import storage, calculations, forecasting, charts

# ----------------------------------------------------------------------
# Page config — must be the first Streamlit call
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Personal Health Analytics",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Custom CSS — modern card-based look
# ----------------------------------------------------------------------
st.markdown("""
<style>

/* Hide Streamlit branding */
#MainMenu, footer {
    visibility: hidden;
}

/* Main App */
.main {
    background: linear-gradient(
                135deg,
                #0F172A 0%,
                #1E1B4B 40%,
                #66001F 100%
                );
}

/* Card */
.metric-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 1.25rem;
}

/* Typography */
.metric-label {
    color: #94A3B8;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-value {
    color: #F8FAFC;
    font-size: 2rem;
    font-weight: 700;
}

.section-title {
    color: #F8FAFC;
    font-size: 1.2rem;
    font-weight: 700;
}

.app-header {
    color: #FFFFFF;
    font-size: 2.4rem;
    font-weight: 800;
}

.app-subheader {
    color: #94A3B8;
    font-size: 1rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0F172A;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-weight: 600;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
}

</style>
""", unsafe_allow_html=True)


def bmi_badge_html(category: str) -> str:
    """Map a BMI category to a colored badge."""
    mapping = {
        "Underweight": "badge-under",
        "Normal weight": "badge-normal",
        "Overweight": "badge-over",
        "Obese": "badge-obese",
    }
    css_class = mapping.get(category, "badge-normal")
    return f'<span class="badge {css_class}">{category}</span>'


def render_metric_card(label: str, value: str, delta: str = None, delta_type: str = "neutral"):
    """Render a single custom metric card (replaces default st.metric for full styling control)."""
    delta_html = ""
    if delta is not None:
        css_class = {"pos": "metric-delta-pos", "neg": "metric-delta-neg"}.get(delta_type, "metric-delta-neutral")
        delta_html = f'<div class="{css_class}">{delta}</div>'

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Load historical data (cached across reruns until a new entry is saved)
# ----------------------------------------------------------------------
if "reload_data" not in st.session_state:
    st.session_state.reload_data = True

df = storage.load_data()
if "dropped_rows" in df.attrs and df.attrs["dropped_rows"] > 0:
    st.warning(f"⚠️ {df.attrs['dropped_rows']} malformed row(s) in the dataset were skipped.")

# ----------------------------------------------------------------------
# Sidebar — input form
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📝 Log Today's Entry")

    with st.form("entry_form", clear_on_submit=False):
        entry_date = st.date_input("Date", value=date.today())
        weight = st.number_input("Weight (kg)", min_value=20.0, max_value=400.0, value=70.0, step=0.1)
        height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.5)
        age = st.number_input("Age", min_value=10, max_value=120, value=25, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        activity_level = st.selectbox("Activity Level", list(calculations.ACTIVITY_MULTIPLIERS.keys()))

        submitted = st.form_submit_button("💾 Save Entry", use_container_width=True)

        if submitted:
            try:
                metrics = calculations.compute_all_metrics(weight, height, age, gender, activity_level)
                entry = {
                    "date": entry_date,
                    "weight_kg": weight,
                    "height_cm": height,
                    "age": age,
                    "gender": gender,
                    "activity_level": activity_level,
                    "bmi": metrics["bmi"],
                    "bmi_category": metrics["bmi_category"],
                    "bmr": metrics["bmr"],
                    "tdee": metrics["tdee"],
                }
                storage.save_entry(entry)
                st.success("Entry saved successfully!")
                st.rerun()
            except ValueError as e:
                st.error(f"Invalid input: {e}")
            except Exception as e:
                st.error(f"Unexpected error while saving: {e}")

    st.divider()
    st.markdown("### 🎯 Target Weight (optional)")
    target_weight = st.number_input(
        "Target weight (kg)", min_value=0.0, max_value=400.0, value=0.0, step=0.5,
        help="Set to 0 to disable target tracking"
    )
    if target_weight == 0.0:
        target_weight = None

# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.markdown('<div class="app-header">🩺 Personal Health Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subheader">Track weight, BMI, and calorie needs over time — with predictive forecasting.</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Empty state
# ----------------------------------------------------------------------
if df.empty:
    st.info("👋 No data yet. Use the sidebar form to log your first entry and the dashboard will populate automatically.")
    st.stop()

latest = storage.get_latest_entry(df)
previous = storage.get_previous_entry(df)

# ----------------------------------------------------------------------
# Top metric cards
# ----------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card("Latest Weight", f"{latest['weight_kg']:.1f} kg")

with col2:
    bmi_val = latest["bmi"]
    render_metric_card("Latest BMI", f"{bmi_val:.1f}")
    st.markdown(bmi_badge_html(latest["bmi_category"]), unsafe_allow_html=True)

with col3:
    if previous is not None:
        weight_change = round(latest["weight_kg"] - previous["weight_kg"], 1)
        delta_type = "pos" if weight_change > 0 else ("neg" if weight_change < 0 else "neutral")
        arrow = "▲" if weight_change > 0 else ("▼" if weight_change < 0 else "—")
        render_metric_card("Weight Change", f"{abs(weight_change):.1f} kg", f"{arrow} vs previous entry", delta_type)
    else:
        render_metric_card("Weight Change", "N/A", "Need 2+ entries", "neutral")

with col4:
    if previous is not None:
        bmi_change = round(latest["bmi"] - previous["bmi"], 2)
        delta_type = "pos" if bmi_change > 0 else ("neg" if bmi_change < 0 else "neutral")
        arrow = "▲" if bmi_change > 0 else ("▼" if bmi_change < 0 else "—")
        render_metric_card("BMI Change", f"{abs(bmi_change):.2f}", f"{arrow} vs previous entry", delta_type)
    else:
        render_metric_card("BMI Change", "N/A", "Need 2+ entries", "neutral")

# ----------------------------------------------------------------------
# Secondary metrics row: ideal weight range, BMR, TDEE
# ----------------------------------------------------------------------
col5, col6, col7 = st.columns(3)
ideal_low, ideal_high = calculations.calculate_ideal_weight_range(latest["height_cm"])

with col5:
    render_metric_card("Ideal Weight Range", f"{ideal_low} – {ideal_high} kg")
with col6:
    render_metric_card("BMR (Basal Metabolic Rate)", f"{latest['bmr']:.0f} kcal/day")
with col7:
    render_metric_card("TDEE (Daily Calorie Needs)", f"{latest['tdee']:.0f} kcal/day")

# ----------------------------------------------------------------------
# Tabs: Trends / Forecast / Raw Data
# ----------------------------------------------------------------------
st.markdown('<div class="section-title">📊 Analytics</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📈 Trends", "🔮 Forecast", "📋 Raw Data"])

with tab1:
    st.plotly_chart(charts.weight_trend_chart(df), use_container_width=True)
    st.plotly_chart(charts.bmi_trend_chart(df), use_container_width=True)

    if len(df) >= 2:
        st.plotly_chart(charts.monthly_progress_chart(df), use_container_width=True)
    else:
        st.caption("📅 Monthly progress chart needs at least 2 entries.")

with tab2:
    forecast_df = forecasting.forecast_weight(df, days_ahead=30)

    if forecast_df is None:
        st.info(
            f"🔮 Forecasting needs at least {forecasting.MIN_POINTS_FOR_FORECAST} entries "
            f"to fit a reliable trend. You currently have {len(df)}."
        )
    else:
        st.plotly_chart(
            charts.forecast_chart(df, forecast_df, target_weight),
            use_container_width=True,
        )

        weekly_trend = forecasting.get_trend_slope_per_week(df)
        colA, colB = st.columns(2)

        with colA:
            trend_label = "gaining" if weekly_trend > 0 else ("losing" if weekly_trend < 0 else "stable")
            render_metric_card("Current Trend", f"{abs(weekly_trend):.2f} kg/week", f"Trend: {trend_label}", "neutral")

        with colB:
            if target_weight is not None:
                target_date = forecasting.estimate_target_date(df, target_weight)
                if target_date is not None:
                    days_away = (target_date.date() - date.today()).days
                    render_metric_card(
                        "Est. Target Date",
                        target_date.strftime("%b %d, %Y"),
                        f"~{max(days_away, 0)} days from today" if days_away >= 0 else "Target already reached",
                        "neutral",
                    )
                else:
                    render_metric_card("Est. Target Date", "Not reachable", "Current trend moves away from target", "neutral")
            else:
                render_metric_card("Est. Target Date", "—", "Set a target weight in the sidebar", "neutral")

with tab3:
    st.dataframe(
        df.sort_values("date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download full history as CSV",
        data=csv_bytes,
        file_name="health_data_export.csv",
        mime="text/csv",
    )

# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------
st.divider()
st.caption("Personal Health Dashboard · Built with Streamlit, Pandas, Plotly & Scikit-Learn · For personal tracking purposes only — not medical advice.")
