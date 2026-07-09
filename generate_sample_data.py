"""
One-off script to generate a realistic sample dataset for the dashboard.
Simulates a person on a gradual weight-loss trajectory over 60 days,
weighing in every 2-3 days (realistic tracking cadence, not daily).
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import calculations

np.random.seed(42)

start_date = date.today() - timedelta(days=60)
height_cm = 175.0
age = 28
gender = "Male"
activity_level = "Moderately active (3-5 days/week)"

# Simulate weight: starts at 82kg, gradual downward trend with realistic noise
starting_weight = 82.0
weekly_loss_rate = 0.4  # kg/week, a healthy realistic rate

rows = []
current_day = 0
while current_day <= 60:
    entry_date = start_date + timedelta(days=current_day)
    trend_weight = starting_weight - (weekly_loss_rate / 7) * current_day
    noise = np.random.normal(0, 0.3)  # daily water-weight fluctuation
    weight = round(trend_weight + noise, 1)

    metrics = calculations.compute_all_metrics(weight, height_cm, age, gender, activity_level)

    rows.append({
        "date": entry_date.isoformat(),
        "weight_kg": weight,
        "height_cm": height_cm,
        "age": age,
        "gender": gender,
        "activity_level": activity_level,
        "bmi": metrics["bmi"],
        "bmi_category": metrics["bmi_category"],
        "bmr": metrics["bmr"],
        "tdee": metrics["tdee"],
    })

    current_day += int(np.random.choice([2, 3]))  # realistic irregular tracking cadence

df = pd.DataFrame(rows)
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "health_data.csv")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_csv(output_path, index=False)
print(f"Generated {len(df)} sample rows -> {output_path}")
