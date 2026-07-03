"""
PDF Report Generator for UK Port Shipping Analysis
Uses ReportLab to produce a styled, print-ready report.
"""

import os
import io
import json
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# Colour palette
NAVY = colors.HexColor("#0F2A5C")
TEAL = colors.HexColor("#0D9488")
AMBER = colors.HexColor("#F59E0B")
LIGHT_GRAY = colors.HexColor("#F3F4F6")
MID_GRAY = colors.HexColor("#9CA3AF")
WHITE = colors.white
RED = colors.HexColor("#EF4444")
GREEN = colors.HexColor("#22C55E")


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "Title", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=26,
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["Normal"],
            fontName="Helvetica", fontSize=12,
            textColor=colors.HexColor("#CBD5E1"), alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "Section", parent=base["Heading1"],
            fontName="Helvetica-Bold", fontSize=14,
            textColor=NAVY, spaceBefore=16, spaceAfter=8,
            borderPad=4,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"],
            fontName="Helvetica", fontSize=10,
            textColor=colors.HexColor("#374151"),
            leading=15, spaceAfter=6,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9,
            textColor=MID_GRAY, alignment=TA_CENTER,
        ),
        "metric_value": ParagraphStyle(
            "MetricValue", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=22,
            textColor=NAVY, alignment=TA_CENTER,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9,
            textColor=WHITE, alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "TableCell", parent=base["Normal"],
            fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#1F2937"), alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "Footer", parent=base["Normal"],
            fontName="Helvetica", fontSize=8,
            textColor=MID_GRAY, alignment=TA_CENTER,
        ),
        "highlight": ParagraphStyle(
            "Highlight", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=10,
            textColor=TEAL,
        ),
    }
    return styles


def _header_footer(canvas, doc):
    """Draw page header band and footer."""
    canvas.saveState()
    w, h = A4

    # Header band
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 60, w, 60, fill=1, stroke=0)

    canvas.setFillColor(TEAL)
    canvas.rect(0, h - 64, w, 4, fill=1, stroke=0)

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawCentredString(w / 2, h - 40, "UK Port Shipping Intelligence Report")
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(w / 2, h - 54, f"Generated: {datetime.now().strftime('%d %B %Y  %H:%M')}")

    # Footer
    canvas.setFillColor(LIGHT_GRAY)
    canvas.rect(0, 0, w, 28, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.rect(0, 28, w, 2, fill=1, stroke=0)
    canvas.setFillColor(MID_GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, 10, "Confidential — UK Shipping Analytics Dashboard")
    canvas.drawRightString(w - 2 * cm, 10, f"Page {doc.page}")

    canvas.restoreState()


def generate_report(predictions_df, metrics: dict, output_path: str) -> str:
    """
    Generate a full PDF analysis report.

    Args:
        predictions_df: DataFrame from predict_next_week()
        metrics: dict from model metrics.json
        output_path: path to save the PDF

    Returns:
        output_path
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    S = _styles()
    story = []
    W, H = A4

    # ── Cover spacer ────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5 * cm))

    # ── Cover block ─────────────────────────────────────────────────────
    cover_data = [[
        Paragraph("🚢 UK Port Shipping", S["title"]),
    ]]
    cover_table = Table(cover_data, colWidths=[16 * cm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [8]),
        ("TOPPADDING", (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 0.3 * cm))

    subtitle_table = Table([[
        Paragraph(f"Weekly Intelligence Report  •  Week of {predictions_df['current_week_ending'].iloc[0]}", S["subtitle"]),
    ]], colWidths=[16 * cm])
    subtitle_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [8]),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(subtitle_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── KPI Metric Cards ────────────────────────────────────────────────
    total_current = int(predictions_df["current_week_count"].sum())
    total_prev = int(predictions_df["prev_week_count"].sum())
    total_predicted = int(predictions_df["predicted_next_week"].sum())
    wk_change = total_current - total_prev
    wk_change_pct = (wk_change / total_prev * 100) if total_prev > 0 else 0

    def kpi_cell(label, value, color=NAVY):
        return [
            Paragraph(label, S["metric_label"]),
            Paragraph(str(value), ParagraphStyle(
                "mv", fontName="Helvetica-Bold", fontSize=20,
                textColor=color, alignment=TA_CENTER,
            )),
        ]

    change_color = GREEN if wk_change >= 0 else RED
    kpi_data = [[
        kpi_cell("PREVIOUS WEEK", total_prev),
        kpi_cell("CURRENT WEEK", total_current),
        kpi_cell("WEEK-ON-WEEK CHANGE", f"{'+'if wk_change>=0 else ''}{wk_change} ({wk_change_pct:+.1f}%)", change_color),
        kpi_cell("PREDICTED NEXT WEEK", total_predicted, TEAL),
    ]]

    kpi_table = Table(kpi_data, colWidths=[4 * cm] * 4, rowHeights=[1.5 * cm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("BOX", (0, 0), (0, -1), 1, NAVY),
        ("BOX", (1, 0), (1, -1), 1, NAVY),
        ("BOX", (2, 0), (2, -1), 1, NAVY),
        ("BOX", (3, 0), (3, -1), 1, TEAL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [6]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Section 1: Per-Port Summary Table ───────────────────────────────
    story.append(Paragraph("📊 Per-Port Shipping Summary", S["section"]))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=8))

    sorted_df = predictions_df.sort_values("current_week_count", ascending=False).reset_index(drop=True)

    header_row = [
        Paragraph("Port", S["table_header"]),
        Paragraph("Prev Week", S["table_header"]),
        Paragraph("Current Week", S["table_header"]),
        Paragraph("Change", S["table_header"]),
        Paragraph("Predicted Next", S["table_header"]),
        Paragraph("Trend", S["table_header"]),
    ]
    table_data = [header_row]

    for _, row in sorted_df.iterrows():
        change = int(row["current_week_count"]) - int(row["prev_week_count"])
        change_str = f"{'+'if change>=0 else ''}{change}"
        trend = "↑" if change > 0 else ("↓" if change < 0 else "→")
        trend_color = GREEN if change > 0 else (RED if change < 0 else MID_GRAY)

        table_data.append([
            Paragraph(str(row["port"]), S["table_cell"]),
            Paragraph(str(int(row["prev_week_count"])), S["table_cell"]),
            Paragraph(str(int(row["current_week_count"])), S["table_cell"]),
            Paragraph(change_str, ParagraphStyle(
                "chg", fontName="Helvetica-Bold", fontSize=9,
                textColor=GREEN if change >= 0 else RED, alignment=TA_CENTER
            )),
            Paragraph(str(int(row["predicted_next_week"])), ParagraphStyle(
                "pred", fontName="Helvetica-Bold", fontSize=9,
                textColor=TEAL, alignment=TA_CENTER
            )),
            Paragraph(trend, ParagraphStyle(
                "trnd", fontName="Helvetica-Bold", fontSize=12,
                textColor=trend_color, alignment=TA_CENTER
            )),
        ])

    col_widths = [3.5 * cm, 2.5 * cm, 2.8 * cm, 2.0 * cm, 2.8 * cm, 2.0 * cm]
    port_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    ts = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, 0), 2, TEAL),
    ])
    port_table.setStyle(ts)
    story.append(port_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Section 2: Top / Bottom Ports ───────────────────────────────────
    story.append(Paragraph("🏆 Traffic Highlights", S["section"]))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=8))

    top3 = sorted_df.head(3)
    bot3 = sorted_df.tail(3)

    highlights_data = [
        [Paragraph("🥇 Highest Traffic Ports (Current Week)", S["table_header"]),
         Paragraph("📉 Lowest Traffic Ports (Current Week)", S["table_header"])],
    ]
    for i in range(3):
        top_row = top3.iloc[i]
        bot_row = bot3.iloc[len(bot3) - 1 - i]
        highlights_data.append([
            Paragraph(
                f"<b>{i+1}. {top_row['port']}</b> — {int(top_row['current_week_count'])} ships",
                S["body"]
            ),
            Paragraph(
                f"<b>{i+1}. {bot_row['port']}</b> — {int(bot_row['current_week_count'])} ships",
                S["body"]
            ),
        ])

    hl_table = Table(highlights_data, colWidths=[8 * cm, 8 * cm])
    hl_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GRAY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(hl_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Section 3: Trend Analysis ────────────────────────────────────────
    story.append(Paragraph("📈 Trend Analysis", S["section"]))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=8))

    gainers = sorted_df[sorted_df["trend_diff"] > 0].sort_values("trend_diff", ascending=False)
    losers = sorted_df[sorted_df["trend_diff"] < 0].sort_values("trend_diff")
    stable = sorted_df[sorted_df["trend_diff"] == 0]

    trend_text = (
        f"Of the <b>{len(sorted_df)}</b> major UK ports tracked this week, "
        f"<b><font color='#{GREEN.hexval()[2:]}'>{len(gainers)}</font></b> ports saw an increase in shipping activity, "
        f"<b><font color='#EF4444'>{len(losers)}</font></b> ports recorded a decline, "
        f"and <b>{len(stable)}</b> remained stable week-on-week. "
    )
    if len(gainers) > 0:
        top_gainer = gainers.iloc[0]
        trend_text += (
            f"The strongest gainer was <b>{top_gainer['port']}</b> "
            f"(+{int(top_gainer['trend_diff'])} ship visits). "
        )
    if len(losers) > 0:
        top_loser = losers.iloc[0]
        trend_text += (
            f"The steepest decline was at <b>{top_loser['port']}</b> "
            f"({int(top_loser['trend_diff'])} ship visits)."
        )

    story.append(Paragraph(trend_text, S["body"]))
    story.append(Spacer(1, 0.3 * cm))

    # Trend table
    trend_header = [
        Paragraph("Port", S["table_header"]),
        Paragraph("WoW Change", S["table_header"]),
        Paragraph("% Change", S["table_header"]),
        Paragraph("Predicted Direction", S["table_header"]),
    ]
    trend_data = [trend_header]
    trend_sorted = sorted_df.sort_values("trend_diff", ascending=False)
    for _, row in trend_sorted.iterrows():
        td = int(row["trend_diff"])
        pct = (td / row["prev_week_count"] * 100) if row["prev_week_count"] > 0 else 0
        pred_dir = "↑ Increasing" if row["predicted_next_week"] > row["current_week_count"] else (
            "↓ Decreasing" if row["predicted_next_week"] < row["current_week_count"] else "→ Stable"
        )
        pd_color = GREEN if "↑" in pred_dir else (RED if "↓" in pred_dir else MID_GRAY)
        trend_data.append([
            Paragraph(str(row["port"]), S["table_cell"]),
            Paragraph(f"{'+'if td>=0 else ''}{td}", ParagraphStyle(
                "td", fontName="Helvetica-Bold", fontSize=9,
                textColor=GREEN if td >= 0 else RED, alignment=TA_CENTER
            )),
            Paragraph(f"{pct:+.1f}%", ParagraphStyle(
                "pct", fontName="Helvetica", fontSize=9,
                textColor=GREEN if pct >= 0 else RED, alignment=TA_CENTER
            )),
            Paragraph(pred_dir, ParagraphStyle(
                "pd", fontName="Helvetica-Bold", fontSize=9,
                textColor=pd_color, alignment=TA_CENTER
            )),
        ])

    tr_table = Table(trend_data, colWidths=[4 * cm, 3.5 * cm, 3 * cm, 5.5 * cm], repeatRows=1)
    tr_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tr_table)
    story.append(PageBreak())

    # ── Section 4: ML Model Performance ─────────────────────────────────
    story.append(Paragraph("🤖 Machine Learning Model Performance", S["section"]))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=8))

    story.append(Paragraph(
        f"The prediction engine uses a <b>Random Forest Regressor</b> trained on "
        f"<b>{metrics.get('n_samples', 'N/A')}</b> weekly observations spanning all major UK ports. "
        f"Features include current and previous week ship counts, 4-week rolling averages, "
        f"week number, month, year, and port identity. "
        f"Model validation uses 5-fold time-series cross-validation to prevent data leakage.",
        S["body"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    # Performance metrics table
    perf_data = [
        [Paragraph("Metric", S["table_header"]),
         Paragraph("Train Score", S["table_header"]),
         Paragraph("CV Mean ± Std", S["table_header"]),
         Paragraph("Interpretation", S["table_header"])],
        [
            Paragraph("MAE (ships)", S["table_cell"]),
            Paragraph(str(metrics.get("mae", "—")), S["table_cell"]),
            Paragraph(f"{metrics.get('cv_mae_mean','—')} ± {metrics.get('cv_mae_std','—')}", S["table_cell"]),
            Paragraph("Lower is better", S["table_cell"]),
        ],
        [
            Paragraph("RMSE (ships)", S["table_cell"]),
            Paragraph(str(metrics.get("rmse", "—")), S["table_cell"]),
            Paragraph(f"{metrics.get('cv_rmse_mean','—')} ± {metrics.get('cv_rmse_std','—')}", S["table_cell"]),
            Paragraph("Lower is better", S["table_cell"]),
        ],
        [
            Paragraph("R² Score", S["table_cell"]),
            Paragraph(str(metrics.get("r2", "—")), S["table_cell"]),
            Paragraph(f"{metrics.get('cv_r2_mean','—')} ± {metrics.get('cv_r2_std','—')}", S["table_cell"]),
            Paragraph("1.0 = perfect", S["table_cell"]),
        ],
    ]

    perf_table = Table(perf_data, colWidths=[3.5 * cm, 3 * cm, 5 * cm, 4.5 * cm])
    perf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(perf_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Section 5: Methodology ───────────────────────────────────────────
    story.append(Paragraph("📋 Methodology & Data Sources", S["section"]))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=8))

    methodology = [
        "<b>Data Source:</b> Weekly Shipping Indicators Dataset (Department for Transport, UK)",
        "<b>Ports Covered:</b> " + ", ".join(predictions_df["port"].tolist()),
        "<b>Time Period:</b> January 2019 – present (weekly cadence)",
        "<b>Model:</b> Random Forest Regressor (300 trees, max depth 12)",
        "<b>Features:</b> Current count, previous count, 2-week lag, 4-week rolling mean, WoW trend, week/month/year, port encoding",
        "<b>Validation:</b> 5-fold TimeSeriesSplit cross-validation",
        "<b>Prediction Target:</b> Next week's ship visit count for each individual port",
    ]
    for item in methodology:
        story.append(Paragraph(f"• {item}", S["body"]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Report generated automatically by UK Shipping Analytics Dashboard  •  {datetime.now().strftime('%d %B %Y')}",
        S["footer"]
    ))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"✅ PDF report saved → {output_path}")
    return output_path


if __name__ == "__main__":
    # Quick test
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from backend.data_processor import load_and_process, get_latest_predictions_input
    from backend.model_trainer import train_model, predict_next_week

    fp = r"C:\Users\ASUS\Downloads\weeklyshippingindicatorsdataset250626.xlsx"
    cleaned, features = load_and_process(fp)
    artifacts = train_model(features)
    pred_input = get_latest_predictions_input(cleaned)
    result = predict_next_week(pred_input, artifacts)

    out = r"C:\Users\ASUS\Downloads\Shipping\reports\shipping_report.pdf"
    generate_report(result, artifacts["metrics"], out)
