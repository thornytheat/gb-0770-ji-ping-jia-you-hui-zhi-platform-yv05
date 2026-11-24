from app.bundles import sample_set
from app.shift import compute


def receipt(dirty,ticket):
    return next(r for r in dirty['balance']['receipts'] if r['ticket']==ticket)


def test_complete_stock_balances(dirty):
    t=dirty['balance']['totals']
    assert t['opening_g']+t['inbound_g']==t['issued_g']+t['closing_g']+t['difference_g']==510000
    assert t['difference_g']==1400


def test_unclosed_truck_has_visible_mass(dirty):
    r=dirty['balance']['stocks'][2]
    assert (r['truck'],r['issued_g'],r['difference_g'])==('FT-23',16000,None)
    assert dirty['balance']['unclosed_mass_g']==16000


def test_variance_exactly_at_allowed_edge(dirty):
    r=receipt(dirty,'T01')
    assert (r['state'],r['variance_g'],r['allowance_g'])==('MATCH',400,400)


def test_short_signed_weight_and_missing_proof(dirty):
    assert (receipt(dirty,'T02')['state'],receipt(dirty,'T02')['variance_g'])==('SIGN_DIFF',-500)
    assert receipt(dirty,'S04')['state']=='NO_RECEIPT'


def test_wrong_truck_and_conflicting_receipts(dirty):
    assert receipt(dirty,'T10')['state']=='SIGN_TRUCK' and receipt(dirty,'T10')['variance_g'] is None
    assert receipt(dirty,'S03')['receipt_lines']==[10,11]
    assert dirty['balance']['unmatched_receipts'][0]['ticket']=='ORPHAN'


def test_faulty_inbound_prevents_complete_stock():
    original=sample_set('clean')
    original['stock']+=b'FT-12,L12BAD,inbound,-\n'
    report=compute(original)['balance']
    assert report['held_trucks']==1 and report['stocks'][0]['isolated_lines']==[9]


def test_clean_has_no_variance_and_no_open_tickets(client):
    out=client.get('/api/balance?sample=clean').json
    assert out['states']=={'MATCH':4} and out['totals']['difference_g']==0
