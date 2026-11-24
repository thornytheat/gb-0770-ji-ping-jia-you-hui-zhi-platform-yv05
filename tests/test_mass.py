from app.conversion.calculate import weigh
from app.meters.catalog import fleet


def one(dirty,ticket):
    return next(row for row in dirty['mass']['rows'] if row['ticket']==ticket)


def test_decimal_small_tickets_sum_exactly(dirty):  # TRAP-10
    grams=[one(dirty,id)['standard']['mass_g'] for id in ('T08','T09','T10')]
    assert grams==[80,80,80] and sum(grams)==240
    assert dirty['mass']['mass_g']==263600


def test_density_units_normalized(dirty):  # TRAP-15
    assert {one(dirty,id)['standard']['density_kg_m3'] for id in ('T01','T02','T07')}=={'800'}
    assert one(dirty,'T05')['fault']['code']=='DENSITY_RANGE'
    assert one(dirty,'UNIT')['fault']['code']=='DENSITY_UNIT'


def test_temperature_changes_volume(dirty):
    r=one(dirty,'T07')['standard']
    assert (r['temperature_factor'],r['liter_at_15_c'],r['mass_g'])==('0.992','99.2',79360)


def test_meter_tolerance_floors_and_rates(dirty):
    assert [one(dirty,ticket)['standard']['allowance_g'] for ticket in ('T01','T02','T07','T08')]==[400,160,199,100]


def test_mass_rounds_one_half_gram_up(dirty):
    row=next(row for row in dirty['readings']['rows'] if row['ticket']=='T08')
    result=weigh([dict(row,volume_l='0.100625')],fleet()[0]['fuels'])
    assert result['mass_g']==81


def test_temperature_outside_calibration_window(dirty):
    row=next(row for row in dirty['readings']['rows'] if row['ticket']=='T08')
    row=dict(row,ticket_record=dict(row['ticket_record'],temp_c='-41'))
    result=weigh([row],fleet()[0]['fuels'])
    assert result['rows'][0]['fault']['code']=='TEMPERATURE'
