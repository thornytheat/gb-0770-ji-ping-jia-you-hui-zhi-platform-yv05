import json

from app.shift import compute


def bundle_evidence(book, files):
    report = compute(files)
    sheets = report['intake']['sheets']
    tickets = {row['data']['ticket'] for row in sheets['tickets']['rows']}
    receipts = {}
    for row in sheets['receipts']['rows']:
        receipts.setdefault(row['data']['ticket'],row['data']['signed_g'])
    with book.connection() as db:
        archived = db.execute("SELECT s.body AS body FROM stage_rows s JOIN shifts h ON h.digest=s.digest "
                              "WHERE s.phase='intake' ORDER BY h.rowid DESC").fetchall()
    for item in archived:
        stored = json.loads(item['body'])['sheets']
        for row in stored['tickets']['rows']:
            tickets.add(row['data']['ticket'])
        for row in stored['receipts']['rows']:
            receipts.setdefault(row['data']['ticket'],row['data']['signed_g'])
    return report,tickets,receipts
