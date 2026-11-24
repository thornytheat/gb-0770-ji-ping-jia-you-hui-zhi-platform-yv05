from decimal import Decimal


def difference(ticket, version):
    opening, closing = Decimal(ticket['start_l']), Decimal(ticket['stop_l'])
    maximum = Decimal(version['range_l'])
    if not 0 <= opening < maximum or not 0 <= closing < maximum:
        return None,'METER_BOUNDS'
    if ticket['event']=='reset':
        return None,'RESET'
    if ticket['event']=='wrap':
        band = Decimal(version['wrap_band_l'])
        if opening < maximum-band or closing >= band or closing >= opening:
            return None,'BAD_WRAP'
        liters = maximum - opening + closing
    else:
        liters = closing-opening
        if liters < 0:
            return None,'REVERSE'
    if liters > Decimal(version['max_ticket_l']):
        return None,'DECLARED_LIMIT'
    return liters,None
