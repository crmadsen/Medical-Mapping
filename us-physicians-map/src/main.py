from data_processing import ensure_database, load_cached_data, filter_and_calculate_distances
from plotting import show_map
import streamlit as st
# Set the page layout to wide
st.set_page_config(page_title="Specialist Physicians Map", layout="wide")

database_path = 'us-physicians-map/data/filtered_physicians.db'
csv_file_path = 'us-physicians-map/data/physicians.csv'
city_state_file_path = 'us-physicians-map/data/city_state.csv'

def main():

    # Ensure the database is created (cached)
    ensure_database(csv_file_path, database_path, city_state_file_path)

    # Load the data (cached)
    data = load_cached_data(database_path)

    # Sidebar for specialty selection
    specialties = data['pri_spec'].unique().tolist()
    selected_specialties = st.sidebar.multiselect(
        "Select Specialties to Display:",
        specialties,
        default=specialties[:3],  # Preselect the first three specialties
        key="unique_specialty_multiselect"  # Use a unique key
    )

    # Initialize session state for previous selection and map load
    if "previous_specialties" not in st.session_state:
        st.session_state.previous_specialties = tuple(selected_specialties)
    if "map_loaded" not in st.session_state:
        st.session_state.map_loaded = False

    # Check if the selection has changed or if the map is being loaded for the first time
    if not st.session_state.map_loaded or tuple(selected_specialties) != st.session_state.previous_specialties:
        # Update session state
        st.session_state.previous_specialties = tuple(selected_specialties)
        st.session_state.map_loaded = True

        # Get the filtered data (cached)
        filtered_data = filter_and_calculate_distances(data, tuple(selected_specialties))

        # Check the size of filtered_data
        print(f"Number of rows in filtered_data: {len(filtered_data)}")
        if filtered_data.empty:
            print("No data available after filtering. Check your filters or data.")
            st.warning("No data available to display on the map.")
            return

        # Define Farmington, NM coordinates
        farmington_lat = 36.7281
        farmington_lon = -108.2187

        # Show the map
        show_map(filtered_data, farmington_lat, farmington_lon)
    else:
        st.info("No changes in specialties. Map remains static.")

if __name__ == "__main__":
    main()