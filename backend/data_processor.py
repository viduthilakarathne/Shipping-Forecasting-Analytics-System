"""
Data Processor for UK Port Shipping Predictions
Loads, cleans, and feature-engineers the weekly shipping Excel data.
"""

import pandas as pd
import numpy as np
import os


# Known UK port GPS coordinates
PORT_COORDINATES = {
    "Grimsby":       {"lat": 53.5685, "lng": -0.0817},
    "London":        {"lat": 51.5074, "lng": 0.0503},
    "Southampton":   {"lat": 50.8974, "lng": -1.4045},
    "Liverpool":     {"lat": 53.4084, "lng": -3.0007},
    "Milford Haven": {"lat": 51.7085, "lng": -5.0455},
    "Felixstowe":    {"lat": 51.9556, "lng": 1.3513},
    "Teesport":      {"lat": 54.5833, "lng": -1.1333},
    "Forth":         {"lat": 56.0000, "lng": -3.7000},
    "Dover":         {"lat": 51.1279, "lng": 1.3134},
    "Belfast":       {"lat": 54.6069, "lng": -5.9068},
    "Holyhead":      {"lat": 53.3083, "lng": -4.6333},
    "Larne":         {"lat": 54.8515, "lng": -5.8235},
    "Warrenpoint":   {"lat": 54.0996, "lng": -6.2512},
    "Portsmouth":    {"lat": 50.7989, "lng": -1.0914},
    "Tyne":          {"lat": 54.9783, "lng": -1.4513},
    "Hull":          {"lat": 53.7444, "lng": -0.3325},
}

PORT_COLUMNS = list(PORT_COORDINATES.keys())

SHEET_WEEKLY_VISITS = "1.Weekly All Visits NSA"
SHEET_WEEKLY_UNIQUE = "2.Weekly All Unique Ships NSA"
HEADER_ROW = 5  # 0-indexed row where headers appear


def load_raw_data(filepath: str) -> dict:
    """Load both main weekly sheets from the Excel file."""
    xl = pd.ExcelFile(filepath)
    visits_df = xl.parse(SHEET_WEEKLY_VISITS, header=HEADER_ROW)
    unique_df = xl.parse(SHEET_WEEKLY_UNIQUE, header=HEADER_ROW)
    return {"visits": visits_df, "unique": unique_df}


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column names, parse dates, drop bad rows."""
    df = df.copy()
    # Strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]

    # Rename 'Week ' -> 'Week'
    if "Week " in df.columns:
        df.rename(columns={"Week ": "Week"}, inplace=True)

    # Drop rows where Week or Week ending is null/non-numeric
    df = df[pd.to_numeric(df["Week"], errors="coerce").notna()]
    df = df[df["Week ending"].notna()]

    # Parse week ending date
    df["week_ending"] = pd.to_datetime(df["Week ending"], dayfirst=True, errors="coerce")
    df = df[df["week_ending"].notna()]

    # Replace '[x]' markers with NaN then interpolate
    for col in PORT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["All of UK"] = pd.to_numeric(df.get("All of UK", np.nan), errors="coerce")
    df["Week"] = pd.to_numeric(df["Week"], errors="coerce").astype(int)

    # Sort chronologically
    df.sort_values("week_ending", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Interpolate missing port values
    for col in PORT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].interpolate(method="linear").round().astype("Int64")

    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create ML-ready per-port feature rows."""
    df = df.copy()
    df["year"] = df["week_ending"].dt.year
    df["month"] = df["week_ending"].dt.month
    df["week_num"] = df["Week"]
    df["week_ending_str"] = df["week_ending"].dt.strftime("%d %b %Y")

    records = []
    for port in PORT_COLUMNS:
        if port not in df.columns:
            continue
        port_df = df[["week_ending", "year", "month", "week_num", port]].copy()
        port_df = port_df.rename(columns={port: "ship_count"})
        port_df["port"] = port
        port_df["lat"] = PORT_COORDINATES[port]["lat"]
        port_df["lng"] = PORT_COORDINATES[port]["lng"]

        port_df.sort_values("week_ending", inplace=True)
        port_df.reset_index(drop=True, inplace=True)

        # Lag features
        port_df["prev_week_count"] = port_df["ship_count"].shift(1)
        port_df["prev2_week_count"] = port_df["ship_count"].shift(2)
        port_df["rolling_mean_4w"] = port_df["ship_count"].shift(1).rolling(4).mean()
        port_df["trend_diff"] = port_df["ship_count"] - port_df["prev_week_count"]

        # Target = next week's count
        port_df["target"] = port_df["ship_count"].shift(-1)

        records.append(port_df)

    feature_df = pd.concat(records, ignore_index=True)
    # Drop rows missing target or lag features
    feature_df.dropna(subset=["target", "prev_week_count", "prev2_week_count"], inplace=True)
    feature_df["target"] = feature_df["target"].astype(float)
    feature_df["ship_count"] = feature_df["ship_count"].astype(float)
    feature_df["prev_week_count"] = feature_df["prev_week_count"].astype(float)
    feature_df["prev2_week_count"] = feature_df["prev2_week_count"].astype(float)
    return feature_df


def load_and_process(filepath: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full pipeline: load → clean → engineer features.
    Returns (cleaned_wide_df, feature_df)
    """
    raw = load_raw_data(filepath)
    cleaned = clean_dataframe(raw["visits"])
    features = engineer_features(cleaned)
    return cleaned, features


def get_latest_predictions_input(cleaned_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each port, extract the most recent two weeks to form the prediction input
    (current week + previous week) for next-week forecasting.
    """
    rows = []
    for port in PORT_COLUMNS:
        if port not in cleaned_df.columns:
            continue
        port_series = cleaned_df[["week_ending", "Week", port]].copy()
        port_series = port_series.rename(columns={port: "ship_count"})
        port_series.sort_values("week_ending", inplace=True)
        port_series.reset_index(drop=True, inplace=True)
        port_series["ship_count"] = pd.to_numeric(port_series["ship_count"], errors="coerce")

        if len(port_series) < 2:
            continue

        last = port_series.iloc[-1]
        prev = port_series.iloc[-2]

        rows.append({
            "port": port,
            "lat": PORT_COORDINATES[port]["lat"],
            "lng": PORT_COORDINATES[port]["lng"],
            "current_week_ending": last["week_ending"].strftime("%d %b %Y"),
            "current_week_count": float(last["ship_count"]),
            "prev_week_count": float(prev["ship_count"]),
            "trend_diff": float(last["ship_count"]) - float(prev["ship_count"]),
            "year": int(last["week_ending"].year),
            "month": int(last["week_ending"].month),
            "week_num": int(last["Week"]),
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    fp = r"C:\Users\ASUS\Downloads\weeklyshippingindicatorsdataset250626.xlsx"
    cleaned, features = load_and_process(fp)
    print(f"Cleaned shape: {cleaned.shape}")
    print(f"Feature rows: {features.shape}")
    print(features[["port", "week_ending", "ship_count", "prev_week_count", "target"]].tail(20))

    pred_input = get_latest_predictions_input(cleaned)
    print("\nPrediction input (latest weeks):")
    print(pred_input.to_string())
