from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

# Bronze
BRONZE_DIR = DATA_DIR / "bronze"
BRONZE_FLIGHTS = BRONZE_DIR / "flights"

BRONZE_REFERENCE = BRONZE_DIR / "reference"
BRONZE_AIRLINES = BRONZE_REFERENCE / "airlines"
BRONZE_AIRPORTS = BRONZE_REFERENCE / "airports"
BRONZE_AIRPORT_IDS = BRONZE_REFERENCE / "airport_ids"

# Silver
SILVER_DIR = DATA_DIR / "silver"
SILVER_FLIGHTS = SILVER_DIR / "flights"

SILVER_REFERENCE = SILVER_DIR / "reference"
SILVER_AIRLINES = SILVER_REFERENCE / "airlines"
SILVER_AIRPORTS = SILVER_REFERENCE / "airports"
SILVER_AIRPORT_IDS = SILVER_REFERENCE / "airport_ids"

# Gold
GOLD_DIR = DATA_DIR / "gold"
GOLD_AIRLINE_RELIABILITY = GOLD_DIR / "airline_reliability"
GOLD_AIRPORT_RELIABILITY = GOLD_DIR / "airport_reliability"
GOLD_ROUTE_RELIABILITY = GOLD_DIR / "route_reliability"
