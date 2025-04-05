# GDELT Events Dashboard

This Streamlit dashboard provides insights on global events using the GDELT (Global Database of Events, Language, and Tone) database through Google BigQuery. The dashboard shows daily events and their social, political, and economic impact scores.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Cloud credentials:
   - Create a Google Cloud project
   - Enable BigQuery API
   - Create a service account and download the JSON key file
   - Rename the key file to `google_credentials.json` and place it in the project root

3. Run the dashboard:
```bash
streamlit run app.py
```

## Features

- Daily event tracking from GDELT database
- Impact analysis with three metrics:
  - Social Impact Score (0-1)
  - Political Impact Score (0-1)
  - Economic Impact Score (0-1)
- Interactive visualizations and filters
- Real-time data updates 