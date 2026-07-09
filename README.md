# 🩺 Personal Health Dashboard

A production-ready health analytics dashboard built with **Streamlit**, **Pandas**, **Plotly**, and **Scikit-Learn** — designed as a portfolio project demonstrating end-to-end data analytics: input → storage → metrics → visualization → forecasting.

This is **not** a toy BMI calculator. It tracks longitudinal health data over time, computes derived metrics (BMR/TDEE via the Mifflin-St Jeor equation), and forecasts future weight trends using linear regression.

---

## ✨ Features

- **Data entry** — weight, height, age, gender, activity level, date, via a sidebar form
- **Health metrics** — BMI, BMI category (WHO classification), ideal weight range, BMR, TDEE
- **Persistent storage** — every entry is appended to a CSV (upserts on same-day duplicates); gracefully handles a missing/corrupt file on first run
- **Dashboard KPIs** — latest weight, latest BMI, weight change, BMI change (deltas vs. previous entry)
- **Interactive Plotly charts** — weight trend, BMI trend (with WHO reference bands), monthly average progress
- **30-day forecast** — linear regression trend projection, weekly rate of change, and estimated date to reach a target weight
- **Modern UI** — custom card-based layout, color-coded BMI badges, tabbed analytics sections

---

## 📂 Project Structure

```
personal-health/
│
├── app.py                     # Main Streamlit app (UI + routing)
├── generate_sample_data.py    # One-off script to regenerate sample dataset
├── data/
│   └── health_data.csv        # Historical records (auto-created if missing)
├── utils/
│   ├── __init__.py
│   ├── storage.py              # CSV load/save, upsert logic, schema handling
│   ├── calculations.py         # BMI, BMR, TDEE, ideal weight (pure functions)
│   ├── forecasting.py          # Linear regression forecasting
│   └── charts.py                # Plotly chart construction
├── requirements.txt
└── README.md
```

**Why this structure:** `app.py` only handles UI/layout and calls into `utils/`. Every module in `utils/` is pure Python with no Streamlit dependency — meaning `calculations.py` and `forecasting.py` are independently unit-testable and reusable (e.g. in a future FastAPI backend) without touching UI code.

---

## 🧮 Metric Formulas

| Metric | Formula |
|---|---|
| BMI | `weight(kg) / height(m)²` |
| BMI Category | WHO thresholds: <18.5 Underweight, 18.5–24.9 Normal, 25–29.9 Overweight, ≥30 Obese |
| Ideal Weight Range | Weight range at BMI 18.5–24.9 for the given height |
| BMR (Mifflin-St Jeor) | Men: `10×weight + 6.25×height − 5×age + 5`; Women: `10×weight + 6.25×height − 5×age − 161` |
| TDEE | `BMR × activity multiplier` (1.2 sedentary → 1.9 extra active) |

---

## 🔮 Forecasting Methodology

- Fits `sklearn.linear_model.LinearRegression` on `(day offset → weight)` pairs from historical entries
- Requires a minimum of **3 data points** to produce a forecast (below that, a linear trend is statistically meaningless — the app shows a message instead of a misleading chart)
- Projects 30 days forward and estimates the calendar date the trend crosses a user-defined target weight
- If the trend is flat or moving away from the target, the app explicitly reports "not reachable" rather than showing a wrong date

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| UI / App Framework | Streamlit |
| Data manipulation | Pandas, NumPy |
| Visualization | Plotly (graph_objects + express) |
| Forecasting | Scikit-Learn (LinearRegression) |
| Storage | CSV (swap-ready for Postgres/SQLite) |

---

## 📌 Known Limitations (by design, for portfolio transparency)

- Single-user, no authentication — this is a personal tracker, not a multi-tenant SaaS
- Forecast is a **linear** trend — doesn't account for plateaus, seasonal effects, or non-linear weight loss curves (a real production version might explore polynomial regression or Prophet if the data volume justified it)
- CSV storage is not concurrency-safe — fine for a single local user, not for concurrent multi-writer access

---

**Disclaimer:** This app is for personal tracking and educational purposes only. It does not constitute medical advice. Consult a healthcare professional for personalized health guidance.
