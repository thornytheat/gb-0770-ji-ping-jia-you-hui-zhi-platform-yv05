from app.diagnostics import RampError
from app.ledger.manifest import lock
from app.ledger.replay import shift
from .document import compile_slip


def sign(book, batch):
    evidence = compile_slip(shift(book,batch))
    checksum = lock(evidence)
    with book.connection() as db:
        inserted = db.execute('INSERT INTO signatures VALUES (?,?) ON CONFLICT(digest) DO NOTHING',(batch,checksum)).rowcount
        saved = db.execute('SELECT checksum FROM signatures WHERE digest=?',(batch,)).fetchone()[0]
    return {'batch':batch,'checksum':saved,'reused':not bool(inserted),
            'open_items':sum(n for key,n in evidence['conservation']['states'].items() if key!='MATCH') +
                         len(evidence['conservation']['unmatched_receipts']),
            'held_trucks':evidence['conservation']['held_trucks']}


def evidence_file(book, batch):
    snapshot = shift(book,batch)
    with book.connection() as db:
        signature = db.execute('SELECT checksum FROM signatures WHERE digest=?',(batch,)).fetchone()
    if signature is None:
        raise RampError('NOT_SIGNED',409)
    document = compile_slip(snapshot)
    return {'checksum':signature[0],'verified':signature[0]==lock(document),'slip':document}
