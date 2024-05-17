# THIS WAS A FIRST TEST IGNORE
import requests
import pickle
import time
import argparse
from tqdm import tqdm

def fetch_publications(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        data = response.json()
        publications = data["_embedded"]["publikacije"]
        return publications
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
        return None

def save_publications(publications, output_file):
    try:
        with open(output_file, "wb") as file:
            pickle.dump(publications, file)
        print(f"Data saved successfully to {output_file}.")
    except IOError as e:
        print(f"Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Fetch publications from the API.")
    parser.add_argument("--url", required=True, help="API endpoint URL")
    parser.add_argument("--output", default="publications.pkl", help="Output file name")
    args = parser.parse_args()

    url = args.url
    output_file = args.output

    all_publications = []

    try:
        with tqdm(desc="Fetching publications", unit="page") as pbar:
            page_number = 1
            while True:
                page_url = f"{url}&pageNumber={page_number}"
                publications = fetch_publications(page_url)

                if publications is None:
                    break

                all_publications.extend(publications)
                page_number += 1
                pbar.update(1)

                time.sleep(1)  # Add a delay between API requests

    except KeyboardInterrupt:
        print("\nProgram interrupted by the user.")

    if all_publications:
        save_publications(all_publications, output_file)
    else:
        print("No publications found.")

if __name__ == "__main__":
    main()
