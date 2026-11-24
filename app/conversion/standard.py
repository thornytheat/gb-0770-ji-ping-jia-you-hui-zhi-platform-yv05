from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from app.configuration import TEMPERATURE_COEFFICIENT

FACTORS = {'kg/m3':Decimal('1'),'kg/L':Decimal('1000'),'g/L':Decimal('1')}
REFERENCE_C = Decimal('15')


def mass(reading, fuels):
    data, version = reading['ticket_record'],reading['version']
    fuel = fuels.get(data['fuel'])
    if fuel is None:
        return None,'FUEL'
    factor = FACTORS.get(data['rho_unit'])
    if factor is None:
        return None,'DENSITY_UNIT'
    rho = Decimal(data['rho'])*factor
    low,high = map(Decimal,fuel['rho_kg_m3'])
    if not low <= rho <= high:
        return None,'DENSITY_RANGE'
    temp = Decimal(data['temp_c'])
    if not Decimal('-40') <= temp <= Decimal('60'):
        return None,'TEMPERATURE'
    correction = 1 - Decimal(TEMPERATURE_COEFFICIENT)*(temp-REFERENCE_C)
    liters_15 = Decimal(reading['volume_l'])*correction
    grams = int((rho*liters_15).to_integral_value(rounding=ROUND_HALF_UP))
    proportional = int((Decimal(grams)*Decimal(version['ppm'])/1000000).to_integral_value(rounding=ROUND_CEILING))
    return {'density_kg_m3':format(rho.normalize(),'f'),'liter_at_15_c':format(liters_15.normalize(),'f'),
            'temperature_factor':format(correction.normalize(),'f'),'mass_g':grams,
            'allowance_g':max(version['floor_g'],proportional)},None
