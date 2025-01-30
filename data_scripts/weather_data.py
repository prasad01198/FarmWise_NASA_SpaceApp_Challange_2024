import logging
import requests
import pandas as pd
import sys
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API configuration for Meteomatics
API_USERNAME = 'YOUR_USERNAME_BY_METOMATICS'  # Replace with your Meteomatics API username
API_PASSWORD = 'YOUR+PASSWORD_BY_METOMATICS'  # Replace with your Meteomatics API password
BASE_URL = 'https://api.meteomatics.com'

# API configuration for OpenCage Geocoding
OPENCAGE_API_KEY = "YOUR_API_KEY"  # Replace with your OpenCage API key

def get_geometry(location):
    """Get geometry for a given location using OpenCage Geocoding API."""
    url = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={OPENCAGE_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data['results']:
            coordinates = data['results'][0]['geometry']
            logging.info(f"Coordinates for {location}: {coordinates}")
            return coordinates['lat'], coordinates['lng']  # Return latitude and longitude
        else:
            logging.error("No results found for the specified location.")
            return None
    else:
        logging.error(f"Geocoding API request failed. Status code: {response.status_code}")
        return None

# Read command-line arguments
if len(sys.argv) != 4:
    print("Usage: python weather_data.py <location> <start_date> <end_date>")
    sys.exit(1)

location = sys.argv[1]  # User-provided location
start_date_str = sys.argv[2]  # User-provided start date
end_date_str = sys.argv[3]  # User-provided end date

# Get latitude and longitude from the location
coordinates = get_geometry(location)
if not coordinates:
    print("Failed to get coordinates for the specified location.")
    sys.exit(1)

lat, lon = coordinates  # Unpack latitude and longitude

# Parse dates
start_date = datetime.strptime(start_date_str, '%m/%d/%Y')
end_date = datetime.strptime(end_date_str, '%m/%d/%Y')
delta = timedelta(days=1)

# Define parameters
parameters = 't_2m:C,precip_1h:mm,wind_speed_10m:ms'
output_format = 'json'

# Prepare an empty list to collect data
weather_data = []

# Loop through the date range
current_date = start_date
while current_date <= end_date:
    # Create the URL for the API request
    date_str = current_date.strftime('%Y-%m-%dT00:00:00Z')
    url = f'{BASE_URL}/{date_str}--{date_str}:PT1H/{parameters}/{lat},{lon}/{output_format}'

    # Send the API request
    response = requests.get(url, auth=(API_USERNAME, API_PASSWORD))

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        # Collect relevant data
        for entry in data['data']:
            for series in entry['coordinates'][0]['dates']:
                weather_data.append({
                    'date': series['date'],
                    'temperature': entry['parameter'].split(':')[0] == 't_2m' and series['value'] or None,
                    'precipitation': entry['parameter'].split(':')[0] == 'precip_1h' and series['value'] or None,
                    'wind_speed': entry['parameter'].split(':')[0] == 'wind_speed_10m' and series['value'] or None,
                })
    else:
        print(f"Error fetching data for {current_date}: {response.status_code} - {response.text}")

    # Move to the next date
    current_date += delta

# Convert collected data into a DataFrame
df = pd.DataFrame(weather_data)

# Save data to a CSV file for visualization
df.to_csv('weather_data.csv', index=False)  # Save the weather data

print('Weather data saved successfully!')
