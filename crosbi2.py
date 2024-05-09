import requests
import pickle
import time
from tqdm import tqdm
import logging
import random

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename="crosbi.log")

def fetch_publications(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        data = response.json()
        publications = data["_embedded"]["publikacije"]
        status_code = response.status_code
        return publications, status_code
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
    url = "https://croris.hr/crosbi-api/publikacija/?pageSize=100"
    output_file = "publications.pkl"
    batch_size = 1000  # Process and save publications in batches of 1000

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.3"
    }

    try:
        with tqdm(desc="Fetching publications", unit="page") as pbar:
            page_number = 1
            retry_count = 0
            batch_publications = []

            while True:
                page_url = f"{url}&pageNumber={page_number}"
                publications, status_code = fetch_publications(page_url, headers)

                if publications is None:
                    retry_count += 1
                    if retry_count <= 9:
                        # Exponential backoff: Wait for an increasing amount of time before retrying
                        backoff_time = 2 ** retry_count + random.uniform(0, 1)
                        logging.info(f"Retrying in {backoff_time:.2f} seconds...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        logging.error("Max retries reached. Stopping the script.")
                        break

                batch_publications.extend(publications)
                page_number += 1
                pbar.update(1)
                retry_count = 0

                logging.info(f"Fetched page {page_number - 1} with status code {status_code}")

                if len(batch_publications) >= batch_size:
                    save_publications(batch_publications, output_file)
                    batch_publications = []

                if len(publications) < 100:
                    # Break the loop if the current page has less than 100 publications
                    break

                time.sleep(random.randint(1, 4))  # Add a configurable delay between API requests

            # Save any remaining publications in the batch
            if batch_publications:
                save_publications(batch_publications, output_file)

    except KeyboardInterrupt:
        logging.info("Program interrupted by the user.")

if __name__ == "__main__":
    main()