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

# BigQuery Settings
GDELT_TABLE = 'gdelt-bq.gdeltv2.events'
QUERY_LIMIT = 1000

# Dashboard Settings
PAGE_TITLE = "GDELT Events Dashboard"
PAGE_ICON = "🌍"
PAGE_LAYOUT = "wide"

# Cache Settings
CACHE_TTL = 3600  # 1 hour 