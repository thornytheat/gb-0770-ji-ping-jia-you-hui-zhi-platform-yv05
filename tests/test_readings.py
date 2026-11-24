from decimal import Decimal
from app.readings.delta import difference


def row(dirty, key):
    return next(x for x in dirty['readings']['rows'] if x['ticket']==key)


def test_recorded_wrap_uses_full_scale(dirty):
    r=row(dirty,'T02')
    assert (r['volume_l'],r['method'],r['version']['range_l'])==('40','wrap','1000')


def test_same_readings_marked_reset_are_not_issued(dirty):
    r=row(dirty,'T03')
    assert r['volume_l'] is None and r['fault']['code']=='RESET'


def test_negative_unclassified_reading(dirty):
    assert row(dirty,'T04')['fault']['code']=='REVERSE'


def test_new_version_restricts_wrap_window(dirty):
    r=row(dirty,'EDGE')
    assert (r['version']['id'],r['fault']['code'])==('F12-2','BAD_WRAP')


def test_exact_rollover_bands(dirty):
    r=row(dirty,'T02')
    t=r['ticket_record']
    assert difference(dict(t,start_l='900',stop_l='99.9'),r['version'])==(Decimal('199.9'),None)
    assert difference(dict(t,start_l='900',stop_l='100'),r['version'])==(None,'BAD_WRAP')


def test_range_maximum_excluded_and_ticket_cap(dirty):
    r=row(dirty,'T02'); t=r['ticket_record']; version=r['version']
    assert difference(dict(t,start_l='1000'),version)==(None,'METER_BOUNDS')
    assert difference(dict(t,event='normal',start_l='1',stop_l='305'),version)==(None,'DECLARED_LIMIT')
