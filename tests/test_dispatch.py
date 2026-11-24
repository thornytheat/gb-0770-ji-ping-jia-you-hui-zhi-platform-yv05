from app.ledger.manifest import lock


def archived(client):
    return '/api/shifts/'+client.post('/api/shifts',json={'sample':'dirty'}).json['batch']


def test_unsigned_batch_cannot_download(client):
    response=client.get(archived(client)+'/export')
    assert (response.status_code,response.json['error'])==(409,'NOT_SIGNED')


def test_certificate_matches_snapshot(client):
    addr=archived(client)
    mark=client.post(addr+'/sign').json
    result=client.get(addr+'/export')
    assert result.json['verified'] and mark['checksum']==lock(result.json['slip'])
    assert result.headers['Content-Disposition'].startswith('attachment;')


def test_signed_evidence_retains_unresolved_items(client):
    addr=archived(client)
    result=client.post(addr+'/sign').json
    assert (result['open_items'],result['held_trucks'])==(12,1)
    evidence=client.get(addr+'/export').json['slip']
    assert evidence['conservation']['unclosed_mass_g']==16000
    assert evidence['sources']['receipts']['isolated']==2


def test_repeat_sign_reuses_same_digest(client):
    addr=archived(client)+'/sign'
    first=client.post(addr).json
    assert client.post(addr).json==dict(first,reused=True)


def test_unknown_signing_target(client):
    result=client.post('/api/shifts/no-such/sign')
    assert (result.status_code,result.json['error'])==(404,'NO_BATCH')


def test_mutated_snapshot_exposed_as_unverified(client,ramp):
    addr=archived(client)
    client.post(addr+'/sign')
    with ramp.book.connection() as db:
        db.execute("UPDATE stage_rows SET body='{}' WHERE phase='balance'")
    assert client.get(addr+'/export').json['verified'] is False
