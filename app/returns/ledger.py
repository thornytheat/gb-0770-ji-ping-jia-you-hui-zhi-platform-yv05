import json
from datetime import datetime, timezone

from app.diagnostics import RampError, detail
from app.intake.schemas import amount
from app.ledger.manifest import lock, serialize
from .evidence import bundle_evidence

ORDER_FIELDS = ('return_id','ticket','truck','weighbill','kg')


def parse_order(raw):
    if not isinstance(raw,dict) or set(raw)!=set(ORDER_FIELDS):
        raise RampError('RETURN_FIELDS')
    order = {}
    for key in ORDER_FIELDS[:-1]:
        value = raw[key]
        if not isinstance(value,str) or not value.strip():
            raise RampError('RETURN_FIELDS')
        order[key] = value.strip()
    kg = raw['kg']
    if not isinstance(kg,str):
        raise RampError('RETURN_FIELDS')
    try:
        grams = int(amount(kg.strip(),exact_grams=True)*1000)
    except ValueError as exc:
        raise RampError('RETURN_FIELDS') from exc
    if grams<=0:
        raise RampError('RETURN_FIELDS')
    order['mass_g'] = grams
    return order


def decide(mass_g, found, signed_g, remaining):
    if not found:
        return 'PENDING','NO_TICKET'
    if signed_g is None:
        return 'PENDING','NO_RECEIPT'
    if mass_g>remaining:
        return 'PENDING','OVER_REMAINING'
    return 'CONFIRMED',None


def get(db, return_id):
    return db.execute('SELECT * FROM returns WHERE return_id=?',(return_id,)).fetchone()


def confirmed_sum(db, ticket):
    row = db.execute("SELECT COALESCE(SUM(mass_g),0) AS total FROM returns WHERE ticket=? AND writeoff='CONFIRMED'",
                     (ticket,)).fetchone()
    return row['total']


def present(row, found, signed_g, remaining):
    return {'return_id':row['return_id'],'ticket':row['ticket'],'truck':row['truck'],
            'weighbill':row['weighbill'],'mass_g':row['mass_g'],'received_at':row['received_at'],
            'inventory':'ENTERED','writeoff':row['writeoff'],
            'reason':detail(row['reason']) if row['reason'] else None,
            'confirmed_g':row['mass_g'] if row['writeoff']=='CONFIRMED' else 0,
            'voucher_checksum':row['checksum'],
            'evidence':{'ticket_found':found,'signed_g':signed_g,'remaining_g':remaining}}


def presented(row, tickets, receipts, db):
    signed = receipts.get(row['ticket'])
    remaining = signed-confirmed_sum(db,row['ticket']) if signed is not None else None
    return present(row,row['ticket'] in tickets,signed,remaining)


def submit(book, files, orders):
    parsed = [parse_order(raw) for raw in orders]
    _,tickets,receipts = bundle_evidence(book,files)
    results = []
    with book.immediate() as db:
        for order in parsed:
            row = get(db,order['return_id'])
            if row is not None:
                if any(row[key]!=order[key] for key in ('ticket','truck','weighbill','mass_g')):
                    raise RampError('RETURN_MISMATCH',409)
                results.append(dict(presented(row,tickets,receipts,db),reused=True))
                continue
            signed = receipts.get(order['ticket'])
            remaining = signed-confirmed_sum(db,order['ticket']) if signed is not None else None
            status,reason = decide(order['mass_g'],order['ticket'] in tickets,signed,remaining)
            db.execute('INSERT INTO returns(return_id,ticket,truck,weighbill,mass_g,received_at,writeoff,reason) '
                       'VALUES (?,?,?,?,?,?,?,?)',
                       (order['return_id'],order['ticket'],order['truck'],order['weighbill'],order['mass_g'],
                        datetime.now(timezone.utc).isoformat(),status,reason))
            results.append(dict(presented(get(db,order['return_id']),tickets,receipts,db),reused=False))
    created = sum(1 for result in results if not result['reused'])
    return {'returns':results,'created':created,'reused':len(results)-created}


def review(book, files, return_id):
    _,tickets,receipts = bundle_evidence(book,files)
    with book.immediate() as db:
        row = get(db,return_id)
        if row is None:
            raise RampError('NO_RETURN',404)
        signed = receipts.get(row['ticket'])
        own = row['mass_g'] if row['writeoff']=='CONFIRMED' else 0
        remaining = signed-(confirmed_sum(db,row['ticket'])-own) if signed is not None else None
        status,reason = decide(row['mass_g'],row['ticket'] in tickets,signed,remaining)
        changed = (status,reason)!=(row['writeoff'],row['reason'])
        if changed:
            db.execute('UPDATE returns SET writeoff=?, reason=? WHERE return_id=?',(status,reason,return_id))
            row = get(db,return_id)
        return dict(presented(row,tickets,receipts,db),changed=changed)


def voucher_of(row, signed_g, remaining):
    return {'document':'退油冲销凭证','return_id':row['return_id'],'ticket':row['ticket'],
            'truck':row['truck'],'weighbill':row['weighbill'],'mass_g':row['mass_g'],
            'received_at':row['received_at'],'inventory':'ENTERED',
            'writeoff':{'status':row['writeoff'],
                        'confirmed_g':row['mass_g'] if row['writeoff']=='CONFIRMED' else 0,
                        'reason':row['reason']},
            'settlement':{'signed_g':signed_g,'remaining_g':remaining}}


def issue_voucher(book, files, return_id):
    _,tickets,receipts = bundle_evidence(book,files)
    with book.immediate() as db:
        row = get(db,return_id)
        if row is None:
            raise RampError('NO_RETURN',404)
        signed = receipts.get(row['ticket'])
        remaining = signed-confirmed_sum(db,row['ticket']) if signed is not None else None
        voucher = voucher_of(row,signed,remaining)
        checksum = lock(voucher)
        reused = row['checksum']==checksum
        if not reused:
            db.execute('UPDATE returns SET voucher=?, checksum=? WHERE return_id=?',
                       (serialize(voucher),checksum,return_id))
    return {'return_id':return_id,'checksum':checksum,'reused':reused,'voucher':voucher}


def fetch_voucher(book, return_id):
    with book.connection() as db:
        row = get(db,return_id)
    if row is None:
        raise RampError('NO_RETURN',404)
    if row['voucher'] is None:
        raise RampError('NO_VOUCHER',409)
    voucher = json.loads(row['voucher'])
    return {'return_id':return_id,'checksum':row['checksum'],
            'verified':row['checksum']==lock(voucher),'voucher':voucher}
