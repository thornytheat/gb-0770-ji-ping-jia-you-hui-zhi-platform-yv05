from collections import Counter
from .inventory import conservation
from .receipts import line_items


def reconcile(weights, intake):
    sheets = intake['sheets']
    findings,unmatched = line_items(weights,sheets['receipts'])
    stocks = conservation(sheets['stock'],findings)
    complete = [row for row in stocks if row['complete']]
    totals = {key:sum(row[key] for row in complete)
              for key in ('opening_g','inbound_g','issued_g','closing_g','difference_g')}
    flags = Counter(row['state'] for row in findings)
    return {'stocks':stocks,'totals':totals,'receipts':findings,'unmatched_receipts':unmatched,'states':dict(flags),
            'complete_trucks':len(complete),'held_trucks':len(stocks)-len(complete),
            'unclosed_mass_g':sum(row['issued_g'] for row in stocks if not row['complete']),
            'receipt_delta_g':sum(row['variance_g'] for row in findings if row['variance_g'] is not None),
            'row_balance':intake['input']==intake['accepted']+intake['isolated']+intake['duplicate'],
            'conserved':totals['opening_g']+totals['inbound_g']==totals['issued_g']+totals['closing_g']+totals['difference_g']}
