from hashlib import sha256
import json

from app.configuration import SAMPLE_PATH
from app.intake.schemas import iso_utc


def fleet():
    raw = (SAMPLE_PATH/'fleet.json').read_bytes()
    book = json.loads(raw)
    for version in book['ranges']:
        version['since'] = iso_utc(version['since'])
        version['until'] = iso_utc(version['until'])
    return book,sha256(raw).hexdigest()
