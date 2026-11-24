from datetime import datetime, timezone
import json
from time import perf_counter

from app.configuration import RULESET,TEMPERATURE_COEFFICIENT
from app.diagnostics import RampError
from app.meters.catalog import fleet
from app.shift import compute
from .manifest import digest,lock,serialize


def replay(book, inputs):
    begin = perf_counter()
    catalog, reference = fleet()
    report = compute(inputs,catalog=catalog)
    setup = {'rules':RULESET,'input_sha256':{name:digest(data) for name,data in inputs.items()},
             'fleet_sha256':reference,'parameters':{'reference_temp_c':15,'thermal_coefficient':TEMPERATURE_COEFFICIENT,
                                                   'mass_unit':'g','shift':'one_bundle'}}
    batch = lock(setup)
    manifest = dict(setup,batch=batch,archived_at=datetime.now(timezone.utc).isoformat(),
                    elapsed_ms=round((perf_counter()-begin)*1000),totals=report['balance']['totals'])
    with book.connection() as db:
        stored = db.execute('INSERT INTO shifts VALUES (?,?) ON CONFLICT(digest) DO NOTHING',(batch,serialize(manifest))).rowcount
        if stored:
            db.executemany('INSERT INTO stage_rows VALUES (?,?,?)',
                           [(batch,phase,serialize(values)) for phase,values in report.items()])
        saved = db.execute('SELECT manifest FROM shifts WHERE digest=?',(batch,)).fetchone()[0]
    return dict(json.loads(saved),reused=not bool(stored))


def list_shifts(book):
    with book.connection() as db:
        return [json.loads(item[0]) for item in db.execute('SELECT manifest FROM shifts ORDER BY rowid DESC LIMIT 25')]


def shift(book, batch):
    with book.connection() as db:
        manifest = db.execute('SELECT manifest FROM shifts WHERE digest=?',(batch,)).fetchone()
        if manifest is None:
            raise RampError('NO_BATCH',404)
        rows = db.execute('SELECT phase,body FROM stage_rows WHERE digest=?',(batch,)).fetchall()
    return {'manifest':json.loads(manifest[0]),'stages':{phase:json.loads(body) for phase,body in rows}}
