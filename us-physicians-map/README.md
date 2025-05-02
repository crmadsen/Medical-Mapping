# U.S. Physicians Map Project

This project visualizes the distribution of U.S. physicians based on their specialties using an interactive map. The data is sourced from a CSV file containing various attributes of physicians, including their names, specialties, and locations.

## Project Structure

```
us-physicians-map
├── data
│   └── physicians.csv        # Dataset of U.S. physicians
├── src
│   ├── main.py               # Entry point of the application
│   ├── data_processing.py     # Functions for loading and filtering data
│   ├── plotting.py            # Functions for plotting data on a map
│   └── utils.py               # Utility functions for data manipulation
├── requirements.txt           # List of dependencies
├── .gitignore                 # Files and directories to ignore in Git
└── README.md                  # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd us-physicians-map
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure that the `data/physicians.csv` file is present in the `data` directory.

## Usage

To run the application, execute the following command:
```
python src/main.py
```

This will load the physician data and display an interactive map where you can select different specialties to visualize their distribution across the U.S.

## Functionality

- **Data Loading**: The project loads physician data from a CSV file.
- **Data Filtering**: Users can filter the data based on physician specialties.
- **Interactive Mapping**: The filtered data is plotted on a map of the U.S., allowing users to explore the distribution of various specialties.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.