# Daily Quality Report Generator

A production-ready Python tool to automatically generate **Daily Quality PDF Reports** for retail stores using images and data fetched from **Google Drive** and **Google Sheets**.

The system validates images, handles missing uploads gracefully, and generates structured, store-wise PDF reports with logs for traceability.

---

## 🚀 Features

- Automated **Daily Quality PDF** generation
- Image validation with fallback placeholder (`not_uploaded.png`)
- Google Drive integration for image download
- Google Sheets integration for store & item data
- Store-wise and date-wise report generation
- Clean logging for debugging and audits

---

## 📂 Project Structure

```
quality_report/
│
├── main.py
├── config.py
├── pdf_generator.py
├── drive_client.py
├── sheets_client.py
├── requirements.txt
├── .gitignore
│
├── assets/
│   └── not_uploaded.png
│
├── data/images/        # ignored
├── output/             # ignored
└── logs/               # ignored
```

---

## ⚙️ Setup Instructions

```bash
git clone git@github.com:d-panshu/Quality-Report.git
cd Quality-Report
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🔐 Google API Setup

Place these files in the project root (not committed to Git):

- credentials.json
- token.json

---

## ▶️ Run the Project

```bash
python main.py
```

Generated PDFs will appear in the `output/` directory.

---


