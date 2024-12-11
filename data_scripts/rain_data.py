import logging
import requests
import json
import pandas as pd
import sys
import time

API_KEY = "dbf974fa35244195bb01be7bb3f1b1bd"  # Use the same API key as in soil_data.py

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_geometry(location):
    """Get geometry for a given location using a geocoding API."""
    url = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data['results']:
            coordinates = data['results'][0]['geometry']
            logging.info(f"Coordinates for {location}: {coordinates}")
            return {
                "type": "Polygon",
                "coordinates": [
                    [
                        [coordinates['lng'] - 0.1, coordinates['lat'] - 0.1],
                        [coordinates['lng'] - 0.1, coordinates['lat'] + 0.1],
                        [coordinates['lng'] + 0.1, coordinates['lat'] + 0.1],
                        [coordinates['lng'] + 0.1, coordinates['lat'] - 0.1],
                        [coordinates['lng'] - 0.1, coordinates['lat'] - 0.1]
                    ]
                ]
            }
        else:
            logging.error("No results found for the specified location.")
            return None
    else:
        logging.error(f"Geocoding API request failed. Status code: {response.status_code}")
        return None

def submit_data_request(datatype, start_date, end_date, geometry):
    url = "https://climateserv.servirglobal.net/api/submitDataRequest/"
    params = {
        "datatype": datatype,
        "begintime": start_date,
        "endtime": end_date,
        "intervaltype": 0,  # Daily interval
        "operationtype": 5,  # Average
        "geometry": json.dumps(geometry),
        "isZip_CurrentDataType": False
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        job_id = response.json()[0]
        logging.info(f"Data request submitted successfully. Job ID: {job_id}")
        return job_id
    else:
        logging.error(f"Failed to submit data request. Status code: {response.status_code}, Response: {response.text}")
        return None

def check_data_request_progress(job_id):
    url = f"https://climateserv.servirglobal.net/api/getDataRequestProgress/?id={job_id}"
    response = requests.get(url)

    if response.status_code == 200:
        progress = response.json()
        logging.info(f"Progress for job {job_id}: {progress}%")
        return progress
    else:
        logging.error(f"Failed to get progress for job {job_id}. Status code: {response.status_code}")
        return None

def get_data_from_request(job_id):
    url = f"https://climateserv.servirglobal.net/api/getDataFromRequest/?id={job_id}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json().get("data", [])
        return data
    else:
        logging.error(f"Failed to retrieve data for job {job_id}. Status code: {response.status_code}")
        return None

if __name__ == "__main__":
    # Command line arguments
    if len(sys.argv) != 4:
        print("Usage: python rain_data.py <location> <start_date> <end_date>")
        sys.exit(1)

    location = sys.argv[1]  # User input for location
    start_date = sys.argv[2]
    end_date = sys.argv[3]

    # Get the geometry from the location
    geometry = get_geometry(location)

    if geometry:
        datatype = 37  # Dataset ID for Rainfall Data
        job_id = submit_data_request(datatype, start_date, end_date, geometry)

        if job_id:
            while True:
                progress = check_data_request_progress(job_id)

                if isinstance(progress, list):
                    progress = progress[0]

                print(f"Data request progress: {progress}%")

                if progress == 100.0:
                    data = get_data_from_request(job_id)
                    if data:
                        df = pd.DataFrame(data)
                        df.to_csv('rainfall_data.csv', index=False)
                        print("Data saved to 'rainfall_data.csv'")
                    else:
                        logging.error("No data returned.")
                    break
                elif progress == -1:
                    print("Failed to process the data request.")
                    break

                time.sleep(10)  # Wait for 10 seconds before checking again
    else:
        print("Failed to get geometry for the specified location.")
