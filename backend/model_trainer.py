"""
ML Model Trainer for UK Port Shipping Count Prediction
Trains a Random Forest Regressor with cross-validation.
Saves model, scaler, and encoder to disk.
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "rf_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "model", "scaler.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "model", "port_encoder.pkl")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "model", "metrics.json")

FEATURE_COLS = [
    "ship_count",       # current week
    "prev_week_count",  # previous week
    "prev2_week_count", # 2 weeks ago
    "rolling_mean_4w",  # rolling average
    "trend_diff",       # current - previous
    "week_num",         # week of year
    "month",            # month of year
    "year",             # year
    "port_encoded",     # encoded port name
]


def prepare_xy(feature_df: pd.DataFrame) -> tuple:
    """Encode categorical port names and scale numerics."""
    df = feature_df.copy()

    # Encode port
    le = LabelEncoder()
    df["port_encoded"] = le.fit_transform(df["port"])

    # Fill any remaining NaN in features with column median
    for col in FEATURE_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    X = df[FEATURE_COLS].values
    y = df["target"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, le, scaler


def train_model(feature_df: pd.DataFrame) -> dict:
    """
    Train Random Forest model.
    Returns dict with model, encoder, scaler, and performance metrics.
    """
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    X, y, le, scaler = prepare_xy(feature_df)

    # Time-series cross-validation
    tscv = TimeSeriesSplit(n_splits=5)

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )

    # Cross-val scores
    cv_mae = -cross_val_score(model, X, y, cv=tscv, scoring="neg_mean_absolute_error")
    cv_rmse = np.sqrt(-cross_val_score(model, X, y, cv=tscv, scoring="neg_mean_squared_error"))
    cv_r2 = cross_val_score(model, X, y, cv=tscv, scoring="r2")

    # Final fit on all data
    model.fit(X, y)

    # In-sample metrics
    y_pred = model.predict(X)
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)

    metrics = {
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "r2": round(float(r2), 4),
        "cv_mae_mean": round(float(cv_mae.mean()), 4),
        "cv_mae_std": round(float(cv_mae.std()), 4),
        "cv_rmse_mean": round(float(cv_rmse.mean()), 4),
        "cv_rmse_std": round(float(cv_rmse.std()), 4),
        "cv_r2_mean": round(float(cv_r2.mean()), 4),
        "cv_r2_std": round(float(cv_r2.std()), 4),
        "n_samples": int(len(y)),
        "n_features": int(len(FEATURE_COLS)),
        "model_type": "RandomForestRegressor",
        "feature_names": FEATURE_COLS,
        "port_classes": list(le.classes_),
    }

    # Save artifacts
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
    with open(ENCODER_PATH, "wb") as f:
        pickle.dump(le, f)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"[OK] Model trained | MAE={mae:.2f} RMSE={rmse:.2f} R2={r2:.4f}")
    print(f"   CV MAE:  {cv_mae.mean():.2f} +/- {cv_mae.std():.2f}")
    print(f"   CV RMSE: {cv_rmse.mean():.2f} +/- {cv_rmse.std():.2f}")
    print(f"   CV R2:   {cv_r2.mean():.4f} +/- {cv_r2.std():.4f}")

    return {
        "model": model,
        "scaler": scaler,
        "encoder": le,
        "metrics": metrics,
    }


def load_model() -> dict:
    """Load saved model, scaler, encoder, and metrics from disk."""
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    with open(ENCODER_PATH, "rb") as f:
        le = pickle.load(f)
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)
    return {"model": model, "scaler": scaler, "encoder": le, "metrics": metrics}


def predict_next_week(pred_input_df: pd.DataFrame, model_artifacts: dict) -> pd.DataFrame:
    """
    Generate next-week predictions for each port.
    pred_input_df: from data_processor.get_latest_predictions_input()
    """
    model = model_artifacts["model"]
    scaler = model_artifacts["scaler"]
    le = model_artifacts["encoder"]

    df = pred_input_df.copy()

    # Encode port name
    df["port_encoded"] = le.transform(df["port"])
    # Approximate 2-week lag and rolling mean from available data
    df["prev2_week_count"] = df["prev_week_count"]
    df["rolling_mean_4w"] = (df["current_week_count"] + df["prev_week_count"]) / 2

    # Build feature matrix matching FEATURE_COLS order:
    # ship_count, prev_week_count, prev2_week_count, rolling_mean_4w,
    # trend_diff, week_num, month, year, port_encoded
    X = np.column_stack([
        df["current_week_count"].values,   # ship_count (current)
        df["prev_week_count"].values,
        df["prev2_week_count"].values,
        df["rolling_mean_4w"].values,
        df["trend_diff"].values,
        df["week_num"].values,
        df["month"].values,
        df["year"].values,
        df["port_encoded"].values,
    ])

    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled)

    df["predicted_next_week"] = np.round(predictions).astype(int)
    return df


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from backend.data_processor import load_and_process, get_latest_predictions_input

    fp = r"C:\Users\ASUS\Downloads\weeklyshippingindicatorsdataset250626.xlsx"
    cleaned, features = load_and_process(fp)
    artifacts = train_model(features)

    pred_input = get_latest_predictions_input(cleaned)
    result = predict_next_week(pred_input, artifacts)
    print("\nNext-week predictions:")
    print(result[["port", "prev_week_count", "current_week_count", "predicted_next_week"]].to_string())
