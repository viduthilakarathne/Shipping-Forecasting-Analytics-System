# 🚢 UK Port Shipping Forecasting & Analytics System

An AI-powered machine learning system that predicts **next week's shipping count** for UK ports using historical weekly shipping data. The system provides an interactive Google Maps dashboard, automated analytics, PDF report generation, and email delivery to support data-driven decision-making in the maritime and logistics industry.

---

## 📖 Project Overview

The UK Port Shipping Forecasting & Analytics System leverages Machine Learning and Time-Series Analysis to forecast weekly shipping traffic at major UK ports.

Users can upload the latest shipping dataset, view predictions on an interactive Google Map, generate analytical reports, and automatically receive those reports via email.

---

## ✨ Key Features

- 📊 Predicts next week's shipping count for each UK port
- 🗺️ Interactive Google Maps visualization
- 📍 Clickable port markers displaying:
  - Previous Week Shipping Count
  - Current Week Shipping Count
  - Predicted Next Week Shipping Count
- 📈 Time-series forecasting using Machine Learning
- 📄 Automatic PDF analysis report generation
- 📧 Email delivery of reports
- 📂 Excel dataset upload and automatic data refresh
- 📉 Trend analysis and shipping performance insights
- 📊 Machine Learning model evaluation metrics

---

## 🤖 Machine Learning Techniques

### Prediction Model
- Random Forest Regressor

### Validation
- Time-Series Cross Validation

### Feature Engineering
- Lag Features
- Rolling Moving Average
- Trend Differencing
- Week-based Features
- Date-based Features

### Data Preprocessing
- Missing Value Imputation (Linear Interpolation)
- StandardScaler
- Label Encoding
- Feature Normalization

---

## 📊 Model Evaluation

The model performance is evaluated using:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- R² Score
- Time-Series Cross Validation

---

## 🗺️ Dashboard Features

The dashboard provides an interactive Google Map displaying UK ports.

Selecting a port displays:

- Port Name
- Previous Week Shipping Count
- Current Week Shipping Count
- Predicted Next Week Shipping Count

Additional dashboard features include:

- Dataset Upload
- Prediction Results
- Trend Analysis
- Report Generation
- Email Report Delivery

---

## 📄 Automated Analysis Report

The system automatically generates a professional PDF report containing:

- Executive Summary
- Current Week Shipping Statistics
- Previous Week Comparison
- Predicted Shipping Counts
- Highest Traffic Ports
- Lowest Traffic Ports
- Weekly Trends
- Machine Learning Performance
- Forecast Summary

---

## 📧 Email Integration

After generating the report, the system automatically sends the PDF to the user's email.

---

## 🛠️ Technologies Used

### Programming Language
- Python

### Machine Learning
- Scikit-learn
- Pandas
- NumPy

### Backend
- FastAPI / Flask

### Frontend
- HTML
- CSS
- JavaScript

### Visualization
- Google Maps API

### Reporting
- ReportLab

### Email Service
- SMTP / Gmail API

---

## 📂 Project Structure

```
Shipping/
│
├── backend/
├── frontend/
├── uploads/
├── reports/
├── requirements.txt
├── run.py
├── START_APP.bat
├── test_pipeline.py
└── README.md
```

---

## 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/viduthilakarathne/Shipping-Forecasting-Analytics-System.git
```

### Navigate to the project

```bash
cd Shipping-Forecasting-Analytics-System
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the application

```bash
python run.py
```

or

```bash
START_APP.bat
```

---

## 📈 Future Improvements

- Deep Learning forecasting models (LSTM, GRU)
- Real-time AIS shipping data integration
- Weather-aware shipping predictions
- Cargo volume forecasting
- Container traffic prediction
- Interactive business dashboard
- Cloud deployment
- REST API integration
- Mobile application support

---

## 🎯 Learning Outcomes

This project demonstrates practical experience in:

- Machine Learning
- Time-Series Forecasting
- Predictive Analytics
- Feature Engineering
- Data Preprocessing
- Data Visualization
- Interactive Dashboard Development
- Google Maps API
- PDF Report Generation
- Email Automation
- Python Backend Development

---

## 👨‍💻 Author

**Vidu Thilakarathne**

Bachelor of Science (Hons) in Information Technology  
Specialization in Data Science  
Sri Lanka Institute of Information Technology (SLIIT)

GitHub:
https://github.com/viduthilakarathne

LinkedIn:
https://www.linkedin.com/in/viduthilakarathne/

---

## 📜 License

This project is developed for educational, research, and portfolio purposes.
