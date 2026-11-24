from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re

COLUMNS = {
    'tickets':('ticket','truck','opened','closed','start_l','stop_l','event','fuel','rho','rho_unit','temp_c'),
    'receipts':('ticket','truck','signed_kg','document'),
    'stock':('truck','movement','kind','kg'),
}
EMPTY_MARKERS = {'','-','N/A','NULL','未知'}
DECIMAL_TEXT = re.compile(r'[+-]?[0-9]{1,10}(?:\.[0-9]{1,6})?')


def amount(text, *, signed=False, exact_grams=False):
    if not DECIMAL_TEXT.fullmatch(text):
        raise ValueError
    value = Decimal(text)
    if (not signed and value<0) or (exact_grams and value*1000 != (value*1000).to_integral_value()):
        raise ValueError
    return value


def iso_utc(text):
    at = datetime.fromisoformat(text)
    if at.utcoffset() is None:
        raise ValueError
    return at.astimezone(timezone.utc).isoformat(timespec='microseconds')


def convert_fields(row, channel):
    if any(value in EMPTY_MARKERS for value in row.values()):
        raise ValueError('SENTINEL')
    try:
        if channel == 'tickets':
            for key in ('opened','closed'):
                row[key] = iso_utc(row[key])
            if row['closed']<=row['opened'] or row['event'] not in ('normal','wrap','reset'):
                raise ValueError
            for key in ('start_l','stop_l','rho','temp_c'):
                row[key] = format(amount(row[key],signed=key=='temp_c').normalize(),'f')
        elif channel == 'receipts':
            row['signed_g'] = int(amount(row.pop('signed_kg'),exact_grams=True)*1000)
        else:
            if row['kind'] not in ('opening','inbound','closing'):
                raise ValueError
            row['mass_g'] = int(amount(row.pop('kg'),exact_grams=True)*1000)
    except (InvalidOperation,ValueError,OverflowError) as exc:
        raise ValueError('MALFORMED') from exc
    return row
