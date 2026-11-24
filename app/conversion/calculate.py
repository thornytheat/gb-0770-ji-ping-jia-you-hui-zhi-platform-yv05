from app.diagnostics import detail
from .standard import mass


def weigh(readings, fuels):
    rows = []
    for reading in readings:
        fault,value = reading['fault'],None
        if not fault:
            value,reason = mass(reading,fuels)
            fault = detail(reason) if reason else None
        rows.append(dict(reading,fault=fault,standard=value))
    verified = [row['standard']['mass_g'] for row in rows if row['standard']]
    return {'rows':rows,'mass_g':sum(verified),'weighed':len(verified),'held':len(rows)-len(verified)}
