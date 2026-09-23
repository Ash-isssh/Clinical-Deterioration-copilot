import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Set seed for reproducibility
np.random.seed(42)

def calculate_news2(hr, sbp, dbp, resp_rate, o2_sat, temp, alert_level):
    """
    Calculate NEWS2 score (simplified).
    Returns: score (0-20 range), risk_category ('low', 'medium', 'high')
    """
    score = 0
    
    # Resp rate
    if resp_rate < 8 or resp_rate > 25:
        score += 3
    elif resp_rate <= 11 or resp_rate >= 21:
        score += 1
    
    # O2 sat
    if o2_sat < 91:
        score += 3
    elif o2_sat < 94:
        score += 2
    elif o2_sat < 96:
        score += 1
    
    # Systolic BP
    if sbp < 90 or sbp > 180:
        score += 3
    elif sbp < 100 or sbp > 160:
        score += 2
    elif sbp <= 110 or sbp >= 150:
        score += 1
    
    # Heart rate
    if hr < 40 or hr > 131:
        score += 3
    elif hr < 50 or hr > 111:
        score += 2
    elif hr <= 90 or hr >= 100:
        score += 1
    
    # Temperature
    if temp < 35 or temp > 39:
        score += 3
    elif temp < 36 or temp > 38.5:
        score += 2
    elif temp < 36.5 or temp > 38.1:
        score += 1
    
    # Alert level
    if alert_level in ['alert', 'confused']:
        score += 3
    elif alert_level in ['voice', 'pain']:
        score += 2
    
    if score <= 4:
        risk = 'low'
    elif score <= 6:
        risk = 'medium'
    else:
        risk = 'high'
    
    return score, risk

def generate_patient_trajectory(patient_id, num_observations, deterioration=False):
    """
    Generate vitals trajectory for a single patient.
    deterioration=True creates a progression toward high risk.
    """
    data = []
    start_time = datetime.now() - timedelta(hours=num_observations)
    
    for i in range(num_observations):
        timestamp = start_time + timedelta(minutes=15*i)
        
        # Baseline vitals (healthy ranges)
        base_hr = np.random.normal(80, 8)
        base_rr = np.random.normal(16, 2)
        base_sbp = np.random.normal(120, 10)
        base_dbp = np.random.normal(80, 8)
        base_o2 = np.random.normal(97, 1.5)
        base_temp = np.random.normal(37, 0.3)
        
        # Deterioration pattern (if enabled)
        if deterioration:
            progress = i / num_observations  # 0 to 1
            # Gradual worsening
            hr = base_hr + (progress * 40)  # increase to ~120
            rr = base_rr + (progress * 10)  # increase to ~26
            sbp = base_sbp - (progress * 30)  # decrease to ~90
            o2 = base_o2 - (progress * 8)  # decrease to ~89
            temp = base_temp + (progress * 2)  # increase to ~39
            alert = 'alert' if progress < 0.7 else ('confused' if progress < 0.9 else 'pain')
        else:
            # Stable patient with minor fluctuations
            hr = base_hr + np.random.normal(0, 3)
            rr = base_rr + np.random.normal(0, 1)
            sbp = base_sbp + np.random.normal(0, 5)
            o2 = base_o2 + np.random.normal(0, 1)
            temp = base_temp + np.random.normal(0, 0.2)
            alert = 'alert'
        
        # Clamp to realistic ranges
        hr = np.clip(hr, 40, 150)
        rr = np.clip(rr, 8, 35)
        sbp = np.clip(sbp, 70, 200)
        o2 = np.clip(o2, 80, 100)
        temp = np.clip(temp, 34, 40)
        dbp = sbp - 40 + np.random.normal(0, 5)
        
        news2_score, risk_cat = calculate_news2(hr, sbp, dbp, rr, o2, temp, alert)
        
        data.append({
            'patient_id': patient_id,
            'timestamp': timestamp.isoformat(),
            'hour_in_study': i * 0.25,  # Each obs is 15 min
            'heart_rate': round(hr, 1),
            'resp_rate': round(rr, 1),
            'sbp': round(sbp, 1),
            'dbp': round(dbp, 1),
            'o2_sat': round(o2, 1),
            'temperature': round(temp, 2),
            'alert_level': alert,
            'news2_score': news2_score,
            'risk_category': risk_cat
        })
    
    return data

def generate_dataset(num_patients=80, observations_per_patient=200, 
                     deterioration_rate=0.25):
    """
    Generate full synthetic dataset.
    
    deterioration_rate: fraction of patients who deteriorate
    """
    all_data = []
    
    for patient_id in range(1, num_patients + 1):
        # ~25% of patients deteriorate
        has_deterioration = np.random.random() < deterioration_rate
        trajectory = generate_patient_trajectory(
            patient_id, 
            observations_per_patient,
            deterioration=has_deterioration
        )
        all_data.extend(trajectory)
    
    df = pd.DataFrame(all_data)
    
    # Generate demographics
    demographics = pd.DataFrame({
        'patient_id': range(1, num_patients + 1),
        'age': np.random.randint(18, 95, num_patients),
        'gender': np.random.choice(['M', 'F'], num_patients),
        'admission_diagnosis': np.random.choice(
            ['Pneumonia', 'CHF', 'Sepsis', 'COPD exacerbation', 'Post-op monitoring'],
            num_patients
        )
    })
    
    return df, demographics

# Generate dataset
print("Generating synthetic dataset...")
vitals_df, demographics_df = generate_dataset(
    num_patients=80,
    observations_per_patient=200,  # ~50 hours per patient (15-min intervals)
    deterioration_rate=0.25
)

# Save to CSV
vitals_df.to_csv('data/raw/synthetic_vitals.csv', index=False)
demographics_df.to_csv('data/patient_profiles/patient_demographics.csv', index=False)

print(f"✓ Generated {len(vitals_df):,} vital observations from {len(demographics_df)} patients")
print(f"  - Vitals CSV: synthetic_vitals.csv ({vitals_df.memory_usage(deep=True).sum() / 1024**2:.1f} MB)")
print(f"  - Demographics CSV: patient_demographics.csv")
print(f"\nDataset breakdown:")
print(f"  - Low risk observations: {(vitals_df['risk_category'] == 'low').sum():,}")
print(f"  - Medium risk observations: {(vitals_df['risk_category'] == 'medium').sum():,}")
print(f"  - High risk observations: {(vitals_df['risk_category'] == 'high').sum():,}")

# Show sample
print(f"\nSample vitals (first 5 observations):")
print(vitals_df.head())

print(f"\nSample demographics:")
print(demographics_df.head())
