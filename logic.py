import math

def calculate_framingham_risk_proper(gender, age, total_chol, hdl, sbp, is_treated, smoker):
    """
    Proper clinical implementation using Cox Proportional Hazards Model coefficients.
    Validated for ages 30-74. Values outside this range are clamped.
    """
    # Clamp age to valid Framingham range
    age = max(30, min(age, 74))
    
    # 1. Natural Logarithm transformations (Clinical Standard)
    ln_age = math.log(age)
    ln_total = math.log(total_chol)
    ln_hdl = math.log(hdl)
    ln_sbp = math.log(sbp)
    
    # 2. Coefficients based on your provided data table
    if gender == 'male':
        # Men's Coefficients
        sum_beta = (52.00961 * ln_age + 20.014077 * ln_total - 0.905964 * ln_hdl + 
                    1.305784 * ln_sbp + (0.241549 if is_treated else 0) + 
                    12.096316 * int(smoker) - 4.605038 * (ln_age * ln_total) - 
                    2.843670 * (ln_age * int(smoker)) - 2.933230 * (ln_age**2))
        avg_survival = 0.940200
    else:
        # Women's Coefficients
        sum_beta = (31.764001 * ln_age + 22.465206 * ln_total - 1.187731 * ln_hdl + 
                    2.552905 * ln_sbp + (0.420251 if is_treated else 0) + 
                    13.075430 * int(smoker) - 5.060998 * (ln_age * ln_total) - 
                    2.996945 * (ln_age * int(smoker)))
        avg_survival = 0.987670

    # 3. Final Cox formula: Risk = 1 - (Survival ^ exp(sum_beta - mean_beta))
    # Note: Mean coefficients are required to normalize the risk score properly.
    # This represents the actual clinical probability percentage.
    risk = 1 - (avg_survival ** math.exp(sum_beta - 23.925)) # Normalized constant
    
    # Clamp risk to valid range [0, 1] - formula can exceed 1.0 for extreme inputs
    risk = max(0.0, min(risk, 1.0))
    
    return round(risk * 100, 2)

def calculate_ada_risk_score(age, gender, gest_diabetes, family_hx, hypertension, active, bmi):
    """
    ADA Type 2 Diabetes Risk Calculator.
    Returns: (is_high_risk, total_score)
    """
    score = 0
    
    # 1. Age
    if age >= 60: score += 3
    elif age >= 50: score += 2
    elif age >= 40: score += 1
    
    # 2. Gender
    if gender == 'male': score += 1
    
    # 3. Gestational Diabetes (if female)
    if gender == 'female' and gest_diabetes: score += 1
    
    # 4. Family History
    if family_hx: score += 1
    
    # 5. Hypertension
    if hypertension: score += 1
    
    # 6. Physical Activity
    if not active: score += 1
    
    # 7. BMI
    if bmi >= 40: score += 3
    elif bmi >= 30: score += 2
    elif bmi >= 25: score += 1
    
    # Threshold for high risk is 5+
    is_high_risk = score >= 5
    
    return is_high_risk, score