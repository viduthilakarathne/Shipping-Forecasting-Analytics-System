"""
test_pipeline.py — Tests the full ML pipeline end-to-end
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\ASUS\Downloads\Shipping')

from backend.data_processor import load_and_process, get_latest_predictions_input
from backend.model_trainer import train_model, predict_next_week
from backend.report_generator import generate_report

print("=== Step 1: Loading & Processing Data ===")
cleaned, features = load_and_process(
    r"C:\Users\ASUS\Downloads\weeklyshippingindicatorsdataset250626.xlsx"
)
print(f"Cleaned data shape: {cleaned.shape}")
print(f"Feature rows: {features.shape}")
ports = features["port"].unique().tolist()
print(f"Ports: {ports}")

print("\n=== Step 2: Training Model ===")
artifacts = train_model(features)
m = artifacts["metrics"]
print(f"  MAE:  {m['mae']}")
print(f"  RMSE: {m['rmse']}")
print(f"  R2:   {m['r2']}")
print(f"  CV MAE:  {m['cv_mae_mean']} +/- {m['cv_mae_std']}")

print("\n=== Step 3: Generating Predictions ===")
pred_input = get_latest_predictions_input(cleaned)
result = predict_next_week(pred_input, artifacts)
print(result[["port", "prev_week_count", "current_week_count", "predicted_next_week"]].to_string())

print("\n=== Step 4: Generating PDF Report ===")
os.makedirs(r"C:\Users\ASUS\Downloads\Shipping\reports", exist_ok=True)
report_path = r"C:\Users\ASUS\Downloads\Shipping\reports\shipping_report.pdf"
generate_report(result, artifacts["metrics"], report_path)
print(f"PDF saved to: {report_path}")
print(f"PDF exists: {os.path.exists(report_path)}")

print("\n=== ALL TESTS PASSED ===")
