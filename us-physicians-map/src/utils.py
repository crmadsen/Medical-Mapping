def clean_specialty(specialty):
    return specialty.strip().title()

def format_location(row):
    return f"{row['City']}, {row['State']}"

def validate_data(row):
    return all([row['Name'], row['Specialty'], row['City'], row['State']])