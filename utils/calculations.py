"""
calculations.py
----------------
Pure functions for health metric calculations.
No Streamlit, no I/O — fully unit-testable in isolation.
"""

from typing import Tuple

# Activity level -> TDEE multiplier (standard Harris-Benedict / Mifflin scaling)
ACTIVITY_MULTIPLIERS = {
    "Sedentary (little or no exercise)": 1.2,
    "Lightly active (1-3 days/week)": 1.375,
    "Moderately active (3-5 days/week)": 1.55,
    "Very active (6-7 days/week)": 1.725,
    "Extra active (athlete / physical job)": 1.9,
}


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """
    BMI = weight(kg) / height(m)^2

    Raises ValueError on non-positive height/weight to fail loudly
    rather than silently producing inf/NaN.
    """
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Height and weight must be positive numbers.")
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


def get_bmi_category(bmi: float) -> str:
    """Standard WHO BMI classification."""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def calculate_ideal_weight_range(height_cm: float) -> Tuple[float, float]:
    """
    Ideal weight range = weight range corresponding to BMI 18.5-24.9
    at the given height. More robust across heights than fixed formulas
    like Devine, which were derived for a narrower population.
    """
    if height_cm <= 0:
        raise ValueError("Height must be a positive number.")
    height_m = height_cm / 100
    low = round(18.5 * (height_m ** 2), 1)
    high = round(24.9 * (height_m ** 2), 1)
    return low, high


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """
    BMR via Mifflin-St Jeor equation — more accurate than Harris-Benedict
    for modern populations.

    Men:   BMR = 10*weight + 6.25*height - 5*age + 5
    Women: BMR = 10*weight + 6.25*height - 5*age - 161
    """
    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        raise ValueError("Weight, height, and age must be positive numbers.")

    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if gender == "Male":
        bmr = base + 5
    elif gender == "Female":
        bmr = base - 161
    else:
        # Non-binary / prefer not to say: average of male/female offsets,
        # a documented, reasonable approximation rather than guessing.
        bmr = base - 78
    return round(bmr, 1)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """TDEE = BMR * activity multiplier."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return round(bmr * multiplier, 1)


def compute_all_metrics(weight_kg: float, height_cm: float, age: int,
                         gender: str, activity_level: str) -> dict:
    """
    Single entry point that computes every derived metric for one
    user input snapshot. Used by app.py to avoid scattering calls.
    """
    bmi = calculate_bmi(weight_kg, height_cm)
    category = get_bmi_category(bmi)
    ideal_low, ideal_high = calculate_ideal_weight_range(height_cm)
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, activity_level)

    return {
        "bmi": bmi,
        "bmi_category": category,
        "ideal_weight_low": ideal_low,
        "ideal_weight_high": ideal_high,
        "bmr": bmr,
        "tdee": tdee,
    }
