import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
import pathlib

from constants import (
    COMMON_COUNTRIES, QUAD_CLASS_CODES, CAMEO_EVENT_CODES,
    PAGE_TITLE, PAGE_ICON, PAGE_LAYOUT
)
from queries import fetch_gdelt_data

# Load environment variables
load_dotenv()

# GDELT Event Code Descriptions
CAMEO_EVENT_CODES = {
    '01': 'MAKE PUBLIC STATEMENT',
    '02': 'APPEAL',
    '03': 'EXPRESS INTENT TO COOPERATE',
    '04': 'CONSULT',
    '05': 'ENGAGE IN DIPLOMATIC COOPERATION',
    '06': 'ENGAGE IN MATERIAL COOPERATION',
    '07': 'PROVIDE AID',
    '08': 'YIELD',
    '09': 'INVESTIGATE',
    '10': 'DEMAND',
    '11': 'DISAPPROVE',
    '12': 'REJECT',
    '13': 'THREATEN',
    '14': 'PROTEST',
    '15': 'EXHIBIT MILITARY POSTURE',
    '16': 'REDUCE RELATIONS',
    '17': 'COERCE',
    '18': 'ASSAULT',
    '19': 'FIGHT',
    '20': 'USE UNCONVENTIONAL MASS VIOLENCE'
}

QUAD_CLASS_CODES = {
    1: "Verbal Cooperation",
    2: "Material Cooperation",
    3: "Verbal Conflict",
    4: "Material Conflict"
}

# Common country codes
COMMON_COUNTRIES = {
    'USA': 'United States',
    'GBR': 'United Kingdom',
    'FRA': 'France',
    'DEU': 'Germany',
    'CHN': 'China',
    'RUS': 'Russia',
    'JPN': 'Japan',
    'IND': 'India',
    'BRA': 'Brazil',
    'CAN': 'Canada',
    'AUS': 'Australia',
    'ZAF': 'South Africa',
    'SAU': 'Saudi Arabia',
    'IRN': 'Iran',
    'ISR': 'Israel',
    'UKR': 'Ukraine',
    'PAK': 'Pakistan',
    'KOR': 'South Korea',
    'MEX': 'Mexico',
    'TUR': 'Turkey'
}

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=PAGE_LAYOUT
)

def check_credentials():
    """Check if Google Cloud credentials are properly set up"""
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path or not pathlib.Path(creds_path).exists():
        st.error("🚫 Google Cloud credentials not found!")
        st.info("""Please follow these steps to set up your credentials:
        1. Go to Google Cloud Console
        2. Create a new project or select an existing one
        3. Enable the BigQuery API
        4. Create a service account and download the JSON key file
        5. Rename the key file to `google_credentials.json`
        6. Place it in the project root directory""")
        return False
    return True

# Initialize Google BigQuery client
@st.cache_resource
def get_bigquery_client():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            scopes=["https://www.googleapis.com/auth/bigquery"],
        )
        return bigquery.Client(credentials=credentials)
    except Exception as e:
        st.error(f"Failed to initialize BigQuery client: {str(e)}")
        return None

# Calculate impact scores based on event attributes
def calculate_impact_scores(row):
    # Social Impact: Based on number of mentions and tone
    social_impact = min(1.0, (row['NumMentions'] / 100) * abs(row['AvgTone']) / 20)
    
    # Political Impact: Based on Goldstein scale and event code
    political_impact = min(1.0, abs(row['GoldsteinScale']) / 10)
    
    # Economic Impact: Based on number of articles and sources
    economic_impact = min(1.0, (row['NumArticles'] / 50) * (row['NumSources'] / 10))
    
    return pd.Series({
        'social_impact': social_impact,
        'political_impact': political_impact,
        'economic_impact': economic_impact
    })

# Fetch GDELT events data
@st.cache_data(ttl=3600)
def fetch_gdelt_data(date):
    client = get_bigquery_client()
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
        `gdelt-bq.gdeltv2.events`
    WHERE
        PARSE_DATE('%Y%m%d', CAST(SQLDATE as STRING)) = '{date}'
    LIMIT 1000
    """
    
    df = client.query(query).to_dataframe()
    
    # Add event descriptions
    df['EventRootDescription'] = df['EventRootCode'].apply(
        lambda x: CAMEO_EVENT_CODES.get(str(x).zfill(2), 'Unknown')
    )
    df['QuadClassDescription'] = df['QuadClass'].apply(
        lambda x: QUAD_CLASS_CODES.get(x, 'Unknown')
    )
    
    # Calculate impact scores
    impact_scores = df.apply(calculate_impact_scores, axis=1)
    df = pd.concat([df, impact_scores], axis=1)
    
    return df

def format_event_summary(row):
    """Create a formatted summary of an event"""
    if row is None or pd.isna(row).all():
        return ""
        
    # Get country names instead of codes
    actor1_country = COMMON_COUNTRIES.get(row.get('Actor1CountryCode', ''), row.get('Actor1CountryCode', 'Unknown'))
    actor2_country = COMMON_COUNTRIES.get(row.get('Actor2CountryCode', ''), row.get('Actor2CountryCode', 'Unknown'))
    
    return f"""
    **Event Type:** {row.get('EventRootDescription', 'Unknown')} ({row.get('EventCode', 'Unknown')})
    **Category:** {row.get('QuadClassDescription', 'Unknown')}
    **Countries Involved:**
    - Primary Actor: {actor1_country} ({row.get('Actor1CountryCode', 'Unknown')})
    - Target Actor: {actor2_country} ({row.get('Actor2CountryCode', 'Unknown')})
    **Specific Location:** {row.get('ActionGeo_FullName', 'Unknown')}
    **Actors:** {row.get('Actor1Name', 'Unknown')} → {row.get('Actor2Name', 'Unknown')}
    **Impact Scores:**
    - Social: {row.get('social_impact', 0):.2f}
    - Political: {row.get('political_impact', 0):.2f}
    - Economic: {row.get('economic_impact', 0):.2f}
    **Additional Info:**
    - Mentions: {row.get('NumMentions', 0)}
    - Sources: {row.get('NumSources', 0)}
    - Tone: {row.get('AvgTone', 0):.2f}
    [Source Article]({row.get('SOURCEURL', '#')})
    ---
    """

# Main dashboard
def main():
    st.title("🌍 GDELT Events Dashboard")
    st.subheader("Global Event Analysis with Impact Scores")
    
    # Check credentials before proceeding
    if not check_credentials():
        return
    
    # Date selector
    default_date = datetime.now().date() - timedelta(days=1)  # Yesterday's date
    selected_date = st.date_input("Select Date", default_date)
    
    try:
        # Initialize BigQuery client
        client = get_bigquery_client()
        if client is None:
            return
            
        # Load data
        with st.spinner("Fetching GDELT events data..."):
            df = fetch_gdelt_data(selected_date)
        
        if df.empty:
            st.warning("No data available for the selected date.")
            return
            
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_social = df['social_impact'].mean()
            st.metric("Average Social Impact", f"{avg_social:.2f}")
            
        with col2:
            avg_political = df['political_impact'].mean()
            st.metric("Average Political Impact", f"{avg_political:.2f}")
            
        with col3:
            avg_economic = df['economic_impact'].mean()
            st.metric("Average Economic Impact", f"{avg_economic:.2f}")
            
        with col4:
            total_events = len(df)
            st.metric("Total Events", total_events)
        
        # Event Type Distribution
        st.subheader("Event Type Distribution")
        event_type_counts = df['EventRootDescription'].value_counts()
        fig = px.pie(
            values=event_type_counts.values,
            names=event_type_counts.index,
            title="Distribution of Event Types"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Country Involvement Analysis
        st.subheader("Country Involvement Analysis")
        
        # Combine both actor country codes and count unique occurrences
        all_countries = pd.concat([
            df['Actor1CountryCode'].map(COMMON_COUNTRIES),
            df['Actor2CountryCode'].map(COMMON_COUNTRIES)
        ]).value_counts().head(10)
        
        fig = px.bar(
            x=all_countries.index,
            y=all_countries.values,
            title="Top 10 Most Involved Countries",
            labels={'x': 'Country', 'y': 'Number of Events'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Event List with Filters
        st.subheader("Detailed Event Summaries")
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        with col1:
            # Get unique countries from both Actor1 and Actor2
            all_countries = sorted(list(set(
                list(df['Actor1CountryCode'].dropna().unique()) + 
                list(df['Actor2CountryCode'].dropna().unique())
            )))
            country_options = ["All"] + [f"{COMMON_COUNTRIES.get(c, c)} ({c})" for c in all_countries if c]
            selected_country = st.selectbox("Filter by Country", country_options)
            
        with col2:
            selected_category = st.selectbox(
                "Filter by Category",
                ["All"] + list(QUAD_CLASS_CODES.values())
            )
        with col3:
            selected_event_type = st.selectbox(
                "Filter by Event Type",
                ["All"] + list(CAMEO_EVENT_CODES.values())
            )
        
        # Filter data based on selection
        filtered_df = df.copy()
        
        # Country filter
        if selected_country != "All":
            country_code = selected_country.split('(')[1].split(')')[0].strip()
            country_mask = (filtered_df['Actor1CountryCode'].fillna('') == country_code) | \
                         (filtered_df['Actor2CountryCode'].fillna('') == country_code)
            filtered_df = filtered_df[country_mask]
        
        # Other filters
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df['QuadClassDescription'] == selected_category]
        if selected_event_type != "All":
            filtered_df = filtered_df[filtered_df['EventRootDescription'] == selected_event_type]
        
        # Show number of filtered events
        st.info(f"Showing {len(filtered_df)} events matching your filters")
        
        # Display event summaries
        for _, row in filtered_df.iterrows():
            summary = format_event_summary(row)
            if summary:
                st.markdown(summary)
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please ensure you have set up your Google BigQuery credentials correctly.")

if __name__ == "__main__":
    main() 