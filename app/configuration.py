import os
from pathlib import Path

SAMPLE_PATH = Path(__file__).resolve().parents[1] / 'sample_data'
BOOK_FILE = os.getenv('FUEL_BOOK', 'var/fuel.sqlite')
RULESET = 'ramp-1.0'
TEMPERATURE_COEFFICIENT = '0.0008'
