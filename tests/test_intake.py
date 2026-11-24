from app.bundles import sample_set
from app.intake.evidence import admit


def test_unicode_bom_preserves_ticket_column(dirty):  # TRAP-02
    assert sample_set('dirty')['tickets'].startswith(b'\xef\xbb\xbf')
    assert dirty['intake']['sheets']['tickets']['rows'][0]['data']['ticket']=='T01'


def test_repeated_header_separates_originals(dirty):  # TRAP-04
    tickets=dirty['intake']['sheets']['tickets']
    assert (tickets['input'],tickets['segments'])==(19,2)
    assert next(row['line'] for row in tickets['rows'] if row['data']['ticket']=='T08')==10


def test_extra_field_does_not_pollute_original(dirty):  # TRAP-05
    records=dirty['intake']['sheets']['tickets']
    assert [(row['line'],row['raw'][-1]) for row in records['quarantine'] if row['code']=='WIDTH']==[(21,'EXTRA')]
    assert records['accepted']==17


def test_missing_instrument_mark_not_zero(dirty):  # TRAP-07
    errors=dirty['intake']['sheets']['tickets']['quarantine']
    assert errors[0]['raw'][4]=='-' and errors[0]['code']=='SENTINEL'


def test_conflicting_receipts_are_both_retained_as_evidence(dirty):  # TRAP-14
    rows=dirty['intake']['sheets']['receipts']['quarantine']
    assert [(r['data']['signed_g'],r['related']) for r in rows]==[(8000,[10,11]),(8200,[10,11])]


def test_decimal_equivalent_receipts_are_duplicates(dirty):
    assert dirty['intake']['sheets']['receipts']['repeat_sources']==[{'line':14,'kept':6}]


def test_clean_receipt_ledger_has_no_quarantine():
    result=admit(sample_set('clean'))
    assert (result['input'],result['accepted'],result['isolated'])==(15,15,0)


def test_missing_bundle_is_rejected(client):
    response=client.post('/api/intake',json={'tickets':'sample'})
    assert (response.status_code,response.json['error'])==(422,'BUNDLE')
