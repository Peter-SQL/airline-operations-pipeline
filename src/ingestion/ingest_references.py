from pathlib import Path
import requests
import csv
import random, time

from config.paths import (
    BRONZE_AIRLINES,
    BRONZE_AIRPORTS,
    BRONZE_AIRPORT_IDS,
)


REFERENCE_FILES = {
    "airlines": {
        "filename": "L_Airline_ID.csv",
        "url": "https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_NVeYVaR_VQ",
        "target_dir": BRONZE_AIRLINES,
    },
    "airports": {
        "filename": "L_Airport.csv",
        "url": "https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_NVecbeg",
        "target_dir": BRONZE_AIRPORTS,
    },
    "airport_ids": {
        "filename": "L_Airport-ID.csv",
        "url": "https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_NVecbeg_VQ",
        "target_dir": BRONZE_AIRPORT_IDS,
    },
}

# These columns should be in the 3 reference tables
EXPECTED_COLUMNS = {"Code", "Description"}


def validate_csv(path: Path) -> bool:

    if not path.exists():
        return False

    if path.stat().st_size == 0:
        return False

    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                return False

            if not EXPECTED_COLUMNS.issubset(set(reader.fieldnames)):
                raise ValueError(
                    f"Unexpected columns in {path.name}. "
                    f"Expected at least: {EXPECTED_COLUMNS}. "
                    f"Found: {set(reader.fieldnames)}"
                )

            first_row = next(reader, None)

            if first_row is None:
                return False

    except (UnicodeDecodeError, csv.Error):
        return False

    return True


def download_reference_file(name: str, config: dict) -> Path:
    filename = config["filename"]
    url = config["url"]

    target_dir = config["target_dir"]
    target_path = target_dir / filename

    if target_path.exists():
        print(f"Already exists: {target_path}")
        return target_path

    print(f"Downloading: {url}", flush= True)

    response = get_with_retries(url)
   
    # Only create folder if needed file is found
    target_dir.mkdir(parents=True, exist_ok=True)

    with open(target_path, "wb") as file:
        file.write(response.content)

    try:
        if not validate_csv(target_path):
            raise ValueError(f"Invalid CSV file: {target_path}")
    except ValueError:
        target_path.unlink(missing_ok=True)
        raise 


    print(f"Validated and saved: {target_path}")

    return target_path





def get_with_retries(url: str, max_retries: int = 5) -> requests.Response:

    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=120)

            if response.status_code == 200:
                return response

            elif response.status_code == 404:
                raise FileNotFoundError(f"File not available: {url}")

            elif response.status_code == 429:
                print("Too many requests — retrying later.")

            elif 400 <= response.status_code < 500:
                response.raise_for_status()

            elif 500 <= response.status_code < 600:
                print(f"Server error {response.status_code} — retrying.")

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise

            print(f"Request failed: {e}")

        wait = (2 ** attempt) + random.uniform(0, 1)
        print(f"Waiting {wait:.2f}s before retry...")
        time.sleep(wait)

    raise RuntimeError(f"All retries exhausted for: {url}")


def main():
    for name, config in REFERENCE_FILES.items():
        try:
            download_reference_file(name, config)
        except Exception as e:
            print(f"{name}: FAILED - {e}")
            raise
        else:
            print(f"{name}: OK")


if __name__ == "__main__":
    main()