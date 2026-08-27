from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

# Bronze
BRONZE_DIR = DATA_DIR / "bronze"

BRONZE_FLIGHTS = BRONZE_DIR / "flights"
BRONZE_REFERENCE = BRONZE_DIR / "reference"


# Silver
SILVER_DIR = DATA_DIR / "silver"

SILVER_FLIGHTS = SILVER_DIR / "flights"
SILVER_REFERENCE = SILVER_DIR / "reference"


# Gold
GOLD_DIR = DATA_DIR / "gold"

GOLD_AIRLINE_RELIABILITY = GOLD_DIR / "airline_reliability"
GOLD_AIRPORT_RELIABILITY = GOLD_DIR / "airport_reliability"
GOLD_ROUTE_RELIABILITY = GOLD_DIR / "route_reliability"
