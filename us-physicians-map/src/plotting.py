import streamlit as st
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

def create_map(filtered_data, farmington_lat, farmington_lon):
    if 'map' not in st.session_state or st.session_state.map is None:
        m = folium.Map(
            location=[farmington_lat, farmington_lon],
            zoom_start=5,
            width='100%',  # Use '100%' for full width or a specific pixel value like '1200px'
            height='800px',  # Use '800px' for a specific height
        )
        
    # Add a marker cluster
    marker_cluster = MarkerCluster().add_to(m)

    # Add markers for each physician
    for _, row in filtered_data.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['Provider First Name']} {row['Provider Last Name']} - {row['pri_spec']}",
        ).add_to(marker_cluster)
        
        st.session_state.map = m  # Save the map in the session state
    return st.session_state.map

def show_map(filtered_data, farmington_lat, farmington_lon):
    m = create_map(filtered_data, farmington_lat, farmington_lon)  # Get or create the map
    folium_static(m)