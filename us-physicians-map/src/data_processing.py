from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pandas as pd
import sqlite3
import os
import unicodedata
import re
import streamlit as st
import numpy as np

def geocode_location(city, state, geolocator, max_retries=3):
    """Geocode a city and state to get latitude and longitude."""
    for attempt in range(max_retries):
        try:
            location = geolocator.geocode(f"{city}, {state}")
            if location:
                return location.latitude, location.longitude
        except GeocoderTimedOut:
            print(f"Geocoding timed out for {city}, {state}. Retrying ({attempt + 1}/{max_retries})...")
    return None, None

def normalize_string(s):
    """Normalize strings by removing accents, converting to lowercase, and stripping extra spaces."""
    if pd.isnull(s):
        return None
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    s = re.sub(r'[^\w\s]', '', s)  # Remove punctuation
    s = s.lower().strip()  # Convert to lowercase and strip whitespace
    return s

def csv_convert(file_path, output_db, city_state_file, keep_columns=None, keep_specialties=None, 
                delete_existing=False):
    # Check if the database file already exists
    if os.path.exists(output_db) and not delete_existing:
        print(f"Database already exists at {output_db}. Skipping conversion.")
        return
    
    if delete_existing and os.path.exists(output_db):
        print(f"Deleting existing database at {output_db}.")
        os.remove(output_db)

    # Specify data types for the columns
    dtype_mapping = {
        'Provider Last Name': 'str',
        'Provider First Name': 'str',
        'pri_spec': 'str',
        'City/Town': 'str',
        'State': 'str'
    }

    # Read the CSV file and filter the columns
    df = pd.read_csv(file_path, dtype=dtype_mapping, low_memory=False)
    if keep_columns:
        existing_columns = [col for col in keep_columns if col in df.columns]
        filtered_df = df[existing_columns]
    else:
        filtered_df = df

    # Filter the DataFrame to include only the specified specialties
    if keep_specialties:
        filtered_df = filtered_df[filtered_df['pri_spec'].isin(keep_specialties)]

    # Load the city-state database
    city_state_df = pd.read_csv(city_state_file)

    # Normalize city and state strings in both DataFrames
    filtered_df['normalized_city'] = filtered_df['City/Town'].apply(normalize_string)
    filtered_df['normalized_state'] = filtered_df['State'].apply(normalize_string)
    city_state_df['normalized_city'] = city_state_df['city_ascii'].apply(normalize_string)
    city_state_df['normalized_state'] = city_state_df['state_id'].apply(normalize_string)

    # Drop duplicate rows in city_state_df based on normalized_city and normalized_state
    city_state_df = city_state_df.drop_duplicates(subset=['normalized_city', 'normalized_state'])

    # Create a dictionary for quick lookup of lat/lng by normalized city and state
    city_state_dict = city_state_df.set_index(['normalized_city', 'normalized_state'])[['lat', 'lng']].to_dict('index')
        
    # Assign latitude and longitude to the physician database
    def get_lat_lng(row):
        key = (row['normalized_city'], row['normalized_state'])
        if key in city_state_dict:
            return pd.Series([city_state_dict[key]['lat'], city_state_dict[key]['lng']])
        return pd.Series([None, None])

    filtered_df[['latitude', 'longitude']] = filtered_df.apply(get_lat_lng, axis=1)

    # Notify if there are unmatched rows
    unmatched_rows = filtered_df[filtered_df['latitude'].isnull() | filtered_df['longitude'].isnull()]
    if not unmatched_rows.empty:
        print(f"Warning: {len(unmatched_rows)} rows could not be matched with the city-state database.")
        print("Unmatched rows (first 5):")
        print(unmatched_rows[['City/Town', 'State']].drop_duplicates().head())

    # Drop the normalized columns
    filtered_df.drop(columns=['normalized_city', 'normalized_state'], inplace=True)

    # Save the filtered data to an SQLite database
    conn = sqlite3.connect(output_db)
    filtered_df.to_sql("physicians", conn, if_exists="replace", index=False)
    conn.close()

    print(f"Filtered data saved to {output_db}")

# Function to load data from the SQLite database
def load_data(file_path, columns=None):
    # Connect to the SQLite database
    conn = sqlite3.connect(file_path)
    
    # Load the data into a DataFrame
    if columns:
        query = f"SELECT {', '.join(columns)} FROM physicians"
    else:
        query = "SELECT * FROM physicians"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

# Function to filter data based on user input
def filter_data(df, specialties):
    # Filter the DataFrame based on the selected specialty
    filtered_df = df[df['pri_spec'] == specialties]
    
    # Add a new column for the full name
    filtered_df['name'] = filtered_df['Provider First Name'] + ' ' + filtered_df['Provider Last Name']
    
    # Drop unnecessary columns
    filtered_df = filtered_df[['name', 'pri_spec', 'City/Town', 'State', 'latitude', 'longitude']]
    
    return filtered_df

@st.cache_data
def ensure_database(csv_file_path, database_path, city_state_file_path):
    csv_convert(
        csv_file_path,
        database_path,
        city_state_file_path,
        keep_columns=['Provider Last Name', 'Provider First Name', 'pri_spec', 'City/Town', 'State', 'latitude', 'longitude'],
        keep_specialties=['CARDIOVASCULAR DISEASE (CARDIOLOGY)', 'ENDOCRINOLOGY', 'GERIATRIC MEDICINE'],
        delete_existing=False  # Avoid deleting the database on every run
    )

@st.cache_data
def load_cached_data(database_path):
    return load_data(database_path)

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the Earth."""
    R = 3958.8  # Radius of Earth in miles
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

@st.cache_data
def filter_and_calculate_distances(data, selected_specialties):
    # Define the coordinates of Farmington, NM
    farmington_lat = 36.7281
    farmington_lon = -108.2187

    print("Executing filter_and_calculate_distances...")
    # Filter the data based on selected specialties
    if selected_specialties:
        filtered_data = data[data['pri_spec'].isin(selected_specialties)]
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no specialties are selected

    # Remove rows with NaN values in latitude or longitude
    filtered_data = filtered_data.dropna(subset=['latitude', 'longitude'])

    # Calculate the distance to Farmington, NM
    filtered_data['distance_to_farmington'] = filtered_data.apply(
        lambda row: haversine(farmington_lat, farmington_lon, row['latitude'], row['longitude']), axis=1
    )

    # Filter to include only doctors within a 300-mile radius
    filtered_data = filtered_data[filtered_data['distance_to_farmington'] <= 500]

    print(f"Filtered data size: {len(filtered_data)}")
    return filtered_data