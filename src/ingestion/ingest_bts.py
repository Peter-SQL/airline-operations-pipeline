from pathlib import Path

import argparse
import requests
import zipfile
import random, time


from config.paths import BRONZE_DIR



BASE_URL = "https://transtats.bts.gov/prezip/"
FILE_PREFIX = "On_Time_Reporting_Carrier_On_Time_Performance_1987_present"


# Example for correct file name: "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2025_1.zip"
def get_filename(year: int, month: int) -> str:
    return f"{FILE_PREFIX}_{year}_{month}.zip"


def get_download_url(year: int, month: int) -> str:
    return BASE_URL + get_filename(year, month)

# Check, whether file is a valid zip-file
def validate_zip(zip_path: Path) -> bool:
    if not zip_path.exists():
        return False

    if zip_path.stat().st_size == 0:
        return False

    if not zipfile.is_zipfile(zip_path):
        return False

    with zipfile.ZipFile(zip_path, "r") as zip_file:
        bad_file = zip_file.testzip()

        if bad_file is not None:
            return False

    return True



def download_period(year: int, month: int) -> tuple [Path, bool]:
    target_dir = (
        BRONZE_DIR
        / "flights"
        / f"year={year}"
        / f"month={month:02d}"
    )


    
    filename = get_filename(year, month)
    zip_path = target_dir / filename
    url = get_download_url(year, month)

    if zip_path.exists():
        print(f"File '{filename}' already exists in path '{target_dir}'")
        return zip_path, False


    print(f"Downloading: {url}", flush= True)

    response = get_with_retries(url)

    if response is None:
        print(f"File not available: {filename}")
        return zip_path, False
    
    # Only create folder if needed file is found
    target_dir.mkdir(parents=True, exist_ok=True)

    with open(zip_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)

    print(f"Saved: {zip_path}")

    if not validate_zip(zip_path):
        zip_path.unlink(missing_ok=True)
        raise ValueError(f"Downloaded file is not a valid ZIP: {zip_path}")

    print("ZIP validation successful.")

    return zip_path, True


def extract_zip(zip_path: Path) -> None:
    target_dir = zip_path.parent

    with zipfile.ZipFile(zip_path, "r") as zip_file:
        zip_file.extractall(target_dir)

    print(f"Extracted to: {target_dir}")


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
    parser = argparse.ArgumentParser(
        description="Download monthly BTS airline data."
    )

    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
  
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Extract downloaded ZIP file."
    )

    args = parser.parse_args()

    if args.year and args.month:
        year, month = args.year, args.month

    else:
        parser.error("Use --year YEAR --month MONTH.")

    if not 1 <= month <= 12:
        parser.error("Month must be between 1 and 12.")

    zip_path, download = download_period(year, month)

    if args.extract and download:
        extract_zip(zip_path)


if __name__ == "__main__":
    main()