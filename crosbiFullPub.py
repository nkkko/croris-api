# this is the 1st version of the script that fetches full publication data from the Croatian Scientific Bibliography (CROSBI) API.
# it was used first on 17th of May 2024 to feetch fullPublications.pkl file with 225331 records based on the results from crosbiAllPub.py and filtered for 20 years to 2024
# to run it: nohup python3 crosbiFullPub.py &

import requests
import pickle
import time
from tqdm import tqdm
import logging
import csv
import random

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename="crosbiFullPub.log")

def fetch_publication(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        data = response.json()
        status_code = response.status_code
        return data, status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Error: {str(e)}")
        return None, None

def save_publications(publications, output_file):
    try:
        with open(output_file, "ab") as file:
            pickle.dump(publications, file)
        logging.info(f"Data saved successfully to {output_file}.")
    except IOError as e:
        logging.error(f"Error: {str(e)}")

def main():
    base_url = "https://croris.hr/crosbi-api/publikacija/"
    output_file = "fullPublications.pkl"
    crosbi_ids_file = "crosbiId.csv"
    batch_size = 1000  # Save publications in batches of 1000

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.3"
    }

    try:
        with open(crosbi_ids_file, "r") as file:
            crosbi_ids = [row[0] for row in csv.reader(file)]

        with tqdm(total=len(crosbi_ids), desc="Fetching publications", unit="publication") as pbar:
            batch_publications = []
            retry_count = 0

            for crosbi_id in crosbi_ids:
                url = f"{base_url}{crosbi_id}"
                publication, status_code = fetch_publication(url, headers)

                if publication is None:
                    retry_count += 1
                    if retry_count <= 9:
                        # Exponential backoff: Wait for an increasing amount of time before retrying
                        backoff_time = 2 ** retry_count + random.uniform(0, 1)
                        logging.info(f"Retrying in {backoff_time:.2f} seconds...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        logging.error(f"Max retries reached. Skipping publication with crosbiId: {crosbi_id}")
                        retry_count = 0
                else:
                    batch_publications.append(publication)
                    logging.info(f"Fetched publication with crosbiId: {crosbi_id}, status code: {status_code}")
                    retry_count = 0

                pbar.update(1)
                time.sleep(0.5)  # Add a 0.5-second delay between API requests

                if len(batch_publications) >= batch_size:
                    save_publications(batch_publications, output_file)
                    batch_publications = []

            # Save any remaining publications in the batch
            if batch_publications:
                save_publications(batch_publications, output_file)

    except KeyboardInterrupt:
        logging.info("Program interrupted by the user.")

if __name__ == "__main__":
    main()