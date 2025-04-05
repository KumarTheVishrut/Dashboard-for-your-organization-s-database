from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import streamlit as st
import os
from constants import GDELT_TABLE, QUERY_LIMIT, CAMEO_EVENT_CODES, QUAD_CLASS_CODES

def get_bigquery_client():
    """Initialize and return a BigQuery client"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            scopes=["https://www.googleapis.com/auth/bigquery"],
        )
        return bigquery.Client(credentials=credentials)
    except Exception as e:
        st.error(f"Failed to initialize BigQuery client: {str(e)}")
        return None

def calculate_impact_scores(row):
    """Calculate impact scores for an event"""
    if row is None:
        return pd.Series({
            'social_impact': 0.0,
            'political_impact': 0.0,
            'economic_impact': 0.0
        })
        
    # Social Impact: Based on number of mentions and tone
    social_impact = min(1.0, (row.get('NumMentions', 0) / 100) * abs(row.get('AvgTone', 0)) / 20)
    
    # Political Impact: Based on Goldstein scale and event code
    political_impact = min(1.0, abs(row.get('GoldsteinScale', 0)) / 10)
    
    # Economic Impact: Based on number of articles and sources
    economic_impact = min(1.0, (row.get('NumArticles', 0) / 50) * (row.get('NumSources', 0)) / 10)
    
    return pd.Series({
        'social_impact': social_impact,
        'political_impact': political_impact,
        'economic_impact': economic_impact
    })

@st.cache_data(ttl=3600)
def fetch_gdelt_data(date):
    """Fetch GDELT events data for a specific date"""
    client = get_bigquery_client()
    if client is None:
        return pd.DataFrame()  # Return empty DataFrame if client initialization fails
        
    query = f"""
    SELECT
        PARSE_DATE('%Y%m%d', CAST(SQLDATE as STRING)) AS EventDate,
        Actor1CountryCode,
        Actor2CountryCode,
        EventCode,
        GoldsteinScale,
        NumMentions,
        NumSources,
        NumArticles,
        AvgTone,
        EventRootCode,
        QuadClass,
        Actor1Name,
        Actor2Name,
        ActionGeo_FullName,
        SOURCEURL
    FROM
        `{GDELT_TABLE}`
    WHERE
        PARSE_DATE('%Y%m%d', CAST(SQLDATE as STRING)) = '{date}'
    LIMIT {QUERY_LIMIT}
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        # Handle empty DataFrame
        if df.empty:
            return df
            
        # Add event descriptions
        df['EventRootDescription'] = df['EventRootCode'].apply(
            lambda x: CAMEO_EVENT_CODES.get(str(x).zfill(2) if pd.notna(x) else '', 'Unknown')
        )
        df['QuadClassDescription'] = df['QuadClass'].apply(
            lambda x: QUAD_CLASS_CODES.get(x if pd.notna(x) else 0, 'Unknown')
        )
        
        # Calculate impact scores
        impact_scores = df.apply(calculate_impact_scores, axis=1)
        df = pd.concat([df, impact_scores], axis=1)
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error 