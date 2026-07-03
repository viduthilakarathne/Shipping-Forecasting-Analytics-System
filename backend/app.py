"""
Flask REST API — UK Port Shipping Analytics Backend
Endpoints:
  GET  /api/status              → server health
  GET  /api/predictions         → latest predictions for all ports
  GET  /api/metrics             → ML model performance metrics
  POST /api/upload              → upload new Excel file and retrain
  POST /api/generate-report     → generate PDF and optionally email it
  GET  /api/download-report     → download latest PDF report
  GET  /api/ports               → port list with coordinates
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import json
import traceback
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from flask import make_response
from werkzeug.utils import secure_filename

# ── Path Setup ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
REPORTS_DIR = BASE_DIR / "reports"
UPLOADS_DIR = BASE_DIR / "uploads"
MODEL_DIR = BACKEND_DIR / "model"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE_DIR))

from backend.data_processor import load_and_process, get_latest_predictions_input, PORT_COORDINATES
from backend.model_trainer import train_model, load_model, predict_next_week
from backend.report_generator import generate_report
from backend.email_sender import send_report_email

# ── Flask App ────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=str(BASE_DIR / "frontend"), static_url_path="")

app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB upload limit

ALLOWED_EXTENSIONS = {"xlsx", "xls"}

# Global state
_data_state = {
    "excel_path": str(BASE_DIR / "uploads" / "dataset.xlsx"),
    "predictions": None,
    "metrics": None,
    "model_artifacts": None,
    "last_trained": None,
    "report_path": None,
}

LATEST_REPORT_PATH = str(REPORTS_DIR / "shipping_report.pdf")

# ── CORS helper ──────────────────────────────────────────────────────────────
@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


# ── Utils ────────────────────────────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def run_pipeline(excel_path: str) -> dict:
    """Load data, train model, generate predictions."""
    cleaned, features = load_and_process(excel_path)
    artifacts = train_model(features)
    pred_input = get_latest_predictions_input(cleaned)
    result_df = predict_next_week(pred_input, artifacts)

    _data_state["predictions"] = result_df
    _data_state["metrics"] = artifacts["metrics"]
    _data_state["model_artifacts"] = artifacts
    _data_state["last_trained"] = datetime.now().isoformat()
    _data_state["excel_path"] = excel_path

    return result_df


def df_to_port_list(df):
    """Convert predictions DataFrame to JSON-serializable list."""
    records = []
    for _, row in df.iterrows():
        records.append({
            "port": str(row["port"]),
            "lat": float(row["lat"]),
            "lng": float(row["lng"]),
            "current_week_ending": str(row["current_week_ending"]),
            "current_week_count": int(row["current_week_count"]),
            "prev_week_count": int(row["prev_week_count"]),
            "trend_diff": int(row["trend_diff"]),
            "predicted_next_week": int(row["predicted_next_week"]),
            "year": int(row["year"]),
            "month": int(row["month"]),
            "week_num": int(row["week_num"]),
        })
    return records


# ── Bootstrap: auto-load default dataset ────────────────────────────────────
def bootstrap():
    """Try to load the bundled dataset on startup."""
    # Check uploads dir first, then Downloads fallback
    candidate_paths = [
        str(UPLOADS_DIR / "dataset.xlsx"),
        r"C:\Users\ASUS\Downloads\weeklyshippingindicatorsdataset250626.xlsx",
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                print(f"🔄 Bootstrapping model from: {p}")
                run_pipeline(p)
                print("✅ Model ready.")
                return
            except Exception as e:
                print(f"⚠️  Bootstrap failed: {e}")
    print("ℹ️  No dataset found at startup. Upload via /api/upload.")


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_file(str(BASE_DIR / "frontend" / "index.html"))


@app.route("/api/status")
def status():
    return jsonify({
        "status": "ok",
        "model_ready": _data_state["predictions"] is not None,
        "last_trained": _data_state["last_trained"],
        "excel_path": _data_state["excel_path"],
    })


@app.route("/api/ports")
def ports():
    return jsonify({
        "ports": [
            {"name": k, "lat": v["lat"], "lng": v["lng"]}
            for k, v in PORT_COORDINATES.items()
        ]
    })


@app.route("/api/predictions")
def predictions():
    if _data_state["predictions"] is None:
        return jsonify({"error": "No predictions available. Upload a dataset first."}), 404
    return jsonify({
        "predictions": df_to_port_list(_data_state["predictions"]),
        "last_trained": _data_state["last_trained"],
    })


@app.route("/api/metrics")
def metrics():
    if _data_state["metrics"] is None:
        return jsonify({"error": "No metrics available."}), 404
    return jsonify(_data_state["metrics"])


@app.route("/api/upload", methods=["POST"])
def upload():
    """Upload a new Excel file and retrain the model."""
    if "file" not in request.files:
        return jsonify({"error": "No file in request. Use multipart/form-data with key 'file'."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only .xlsx / .xls files are accepted."}), 400

    filename = "dataset.xlsx"
    save_path = str(UPLOADS_DIR / filename)
    file.save(save_path)

    try:
        result_df = run_pipeline(save_path)
        return jsonify({
            "success": True,
            "message": f"File processed. Model retrained on {len(result_df)} ports.",
            "ports": df_to_port_list(result_df),
            "metrics": _data_state["metrics"],
            "last_trained": _data_state["last_trained"],
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate-report", methods=["POST"])
def generate_report_endpoint():
    """Generate PDF and optionally send via email."""
    if _data_state["predictions"] is None:
        return jsonify({"error": "No predictions. Upload dataset first."}), 400

    body = request.get_json(silent=True) or {}
    send_email = body.get("send_email", False)
    sender_email = body.get("sender_email", "")
    sender_password = body.get("sender_password", "")
    recipient_email = body.get("recipient_email", "")

    try:
        report_path = LATEST_REPORT_PATH
        generate_report(
            _data_state["predictions"],
            _data_state["metrics"],
            report_path,
        )
        _data_state["report_path"] = report_path

        result = {"success": True, "report_path": report_path}

        if send_email and sender_email and recipient_email:
            email_result = send_report_email(
                sender_email=sender_email,
                sender_password=sender_password,
                recipient_email=recipient_email,
                pdf_path=report_path,
                week_ending=_data_state["predictions"]["current_week_ending"].iloc[0],
            )
            result["email"] = email_result

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/download-report")
def download_report():
    """Stream the latest generated PDF to the browser."""
    if not os.path.exists(LATEST_REPORT_PATH):
        return jsonify({"error": "No report generated yet."}), 404
    return send_file(
        LATEST_REPORT_PATH,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"UK_Shipping_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
    )


# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bootstrap()
    print("🚀 Starting Flask server on http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
