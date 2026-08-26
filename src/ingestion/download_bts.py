from pathlib import Path
import argparse
import re
import zipfile

import requests

BRONZE_DIR = Path("data/bronze")



BASE_URL = "https://transtats.bts.gov/prezipace/"
FILE_PREFIX = "aceOn_Time_Reporting_Carrier_On_Time_Performance_1987_present"


# Example for correct file name: "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2025_1.zip"
def get_filename(year: int, month: int) -> str:
    return f"{FILE_PREFIX}_{year}_{month}.zip"

def get_download_url(year: int, month: int) -> str:
    return BASE_URL + get_filename(year, month)


def download_period(year: int, month: int) -> Path:
    target_dir = BRONZE_DIR / f"{year}-{month:02d}"
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = get_filename(year, month)
    zip_path = target_dir / filename
    url = get_download_url(year, month)

    if zip_path.exists():
        print(f"File {zip_path} already exists")
        return zip_path


    print(f"Downloading: {url}")

    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()

    print(raise_for_status())

    with open(zip_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)

    print(f"Saved: {zip_path}")

    return zip_path


def extract_zip(zip_path: Path) -> None:
    target_dir = zip_path.parent

    with zipfile.ZipFile(zip_path, "r") as zip_file:
        zip_file.extractall(target_dir)

    print(f"Extracted to: {target_dir}")


# def get_latest_available_month() -> tuple[int, int]:
#     response = requests.get(BASE_URL, timeout=30)
#     response.raise_for_status()

#     pattern = re.compile(
#         rf"{re.escape(FILE_PREFIX)}_(\d{{4}})_(\d{{1,2}})\.zip"
#     )

#     matches = pattern.findall(response.text)

#     if not matches:
#         raise RuntimeError("No BTS monthly files found.")

#     periods = [(int(year), int(month)) for year, month in matches]

#     return max(periods)


def main():
    parser = argparse.ArgumentParser(
        description="Download BTS monthly airline on-time data."
    )

    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Download latest available BTS month."
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Extract downloaded ZIP file."
    )

    args = parser.parse_args()

    if args.latest:
        year, month = get_latest_available_month()
        print(f"Latest BTS month: {year}-{month:02d}")

    elif args.year and args.month:
        year, month = args.year, args.month

    else:
        parser.error("Use --year YEAR --month MONTH or --latest.")

    if not 1 <= month <= 12:
        parser.error("Month must be between 1 and 12.")

    zip_path = download_period(year, month)

    if args.extract:
        extract_zip(zip_path)


if __name__ == "__main__":
    main()

