from pathlib import Path
import requests
import csv
import time
from config.paths import BRONZE_DIR


REFERENCE_FILES = {
    "airlines": {
        "filename": "L_Airline_ID.csv",
        "url": "https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_NVeYVaR_VQ",
    },
    "airports": {
        "filename": "L_Airport.csv",
        "url": "https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_NVecbeg",
    },
    "airport_ids": {
        "filename": "L_Airport-ID.csv",
        "url": "https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_NVecbeg_VQ",
    },
}


def validate_csv(path: Path) -> bool:
    if not path.exists():
        return False

    if path.stat().st_size == 0:
        return False

    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)

            header = next(reader, None)

            if not header:
                return False

            first_row = next(reader, None)

            if first_row is None:
                return False

    except (UnicodeDecodeError, csv.Error):
        return False

    return True





def download_reference_file(name: str, config: dict) -> Path:
    filename = config["filename"]
    url = config["url"]

    target_dir = BRONZE_DIR / "reference" / name
    target_path = target_dir / filename

    if target_path.exists():
        print(f"Already exists: {target_path}")
        return target_path

    print(f"Downloading: {url}", flush= True)

    response = get_with_retries(url)

    if response is None:
        print(f"File not available: {filename}")
        return target_path, False
    
    # Only create folder if needed file is found
    target_dir.mkdir(parents=True, exist_ok=True)

    with open(target_path, "wb") as file:
        file.write(response.content)

        print(1)
        time.sleep(23)
        print(2)

    if not validate_csv(target_path):
        target_path.unlink(missing_ok=True)
        raise ValueError(f"Invalid CSV file: {target_path}")

    print(f"Validated and saved: {target_path}")




    # if not validate_zip(zip_path):
    #     zip_path.unlink(missing_ok=True)
    #     raise ValueError(f"Downloaded file is not a valid ZIP: {zip_path}")

    # print("ZIP validation successful.")

   # return target_path 


def get_with_retries(url: str, max_retries: int = 5) -> requests.Response:

    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=120)

            if response.status_code == 200:
                return response

            elif response.status_code == 404:
                print("File not available yet — retrying.")

            elif response.status_code == 429:
                print("Too many requests — retrying later.")

            elif 400 <= response.status_code < 500:
                print(f"Client error {response.status_code}.")

            elif 500 <= response.status_code < 600:
                print(f"Server error {response.status_code} — retrying.")

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise

            print(f"Request failed: {e}")

        wait = (2 ** attempt) + random.uniform(0, 1)
        print(f"Waiting {wait:.2f}s before retry...")
        time.sleep(wait)

    print("All retries exhausted.")
    return None


def main():
    for name, config in REFERENCE_FILES.items():
        download_reference_file(name, config)


if __name__ == "__main__":
    main()