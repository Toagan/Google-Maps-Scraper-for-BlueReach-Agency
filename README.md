# 🗺️ Google Maps Scraper for BlueReach Agency

This repository contains a Python script that scrapes business listings across all German cities using the **Serper.dev** Google Maps API. It helps extract detailed contact data by keyword (e.g., "Handwerker", "Zahnarzt") and saves the results to a CSV file.

---

## 🚀 Features

- 🔍 Search any keyword (e.g., industry or profession)
- 🇩🇪 Targets **all cities in Germany** using population data
- 🔁 Resume scraping from last run using checkpointing
- 💾 Saves unique business entries with deduplication
- 📁 Exports results to `output/business_entries_<keyword>.csv`
- 🧠 Smart pagination logic based on city population

---

## 📦 Requirements

- Python 3.8+
- Dependencies (install with `pip install -r requirements.txt`)
- A [Serper.dev API key](https://serper.dev)

---

## 🏁 How to Run

1. Place `cities1000.txt` (from [GeoNames](https://download.geonames.org/export/dump/)) in the root folder.

2. Run the script:
```bash
python maps_scraper.py
