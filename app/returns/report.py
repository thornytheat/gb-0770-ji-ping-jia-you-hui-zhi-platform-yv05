from collections import defaultdict

from app.diagnostics import detail
from .evidence import bundle_evidence
from .ledger import presented


def returns_report(book, files):
    report,tickets,receipts = bundle_evidence(book,files)
    with book.connection() as db:
        rows = db.execute('SELECT * FROM returns ORDER BY received_at,return_id').fetchall()
        returns = [presented(row,tickets,receipts,db) for row in rows]
    returned = defaultdict(int)
    for row in rows:
        returned[row['truck']] += row['mass_g']
    stocks, seen = [],set()
    for stock in report['balance']['stocks']:
        truck = stock['truck']
        seen.add(truck)
        inbound = returned.get(truck,0)
        physical = (stock['opening_g']+stock['inbound_g']+inbound-stock['issued_g']-stock['closing_g']
                    if stock['complete'] else None)
        stocks.append(dict(stock,returned_g=inbound,physical_difference_g=physical))
    for truck in sorted(set(returned)-seen):
        stocks.append({'truck':truck,'opening_g':None,'inbound_g':None,'issued_g':None,'closing_g':None,
                       'difference_g':None,'complete':False,'fault':detail('STOCK_ANCHORS'),
                       'source_lines':[],'isolated_lines':[],
                       'returned_g':returned[truck],'physical_difference_g':None})
    totals = {'orders':len(rows),'returned_g':sum(row['mass_g'] for row in rows),
              'confirmed_g':sum(row['mass_g'] for row in rows if row['writeoff']=='CONFIRMED'),
              'pending_g':sum(row['mass_g'] for row in rows if row['writeoff']=='PENDING'),
              'pending':sum(1 for row in rows if row['writeoff']=='PENDING')}
    return {'returns':returns,'stocks':stocks,'totals':totals}
