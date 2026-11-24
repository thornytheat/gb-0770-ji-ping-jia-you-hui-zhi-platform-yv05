from app.bundles import sample_set
from app.intake.evidence import channel_report


def test_gb18030_stock_parses_native_reference():
    provided='truck,movement,kind,kg\nFT-12,进油甲,inbound,1.001\n'.encode('gb18030')
    row=channel_report('stock',provided)['rows'][0]['data']
    assert (row['movement'],row['mass_g'])==('进油甲',1001)


def test_three_distinct_empty_states(client):
    data={key:value.decode() for key,value in sample_set('clean').items()}
    for raw,expected in [('', 'EMPTY_FILE'),('  ', 'BLANK_FILE'),(data['stock'].splitlines()[0], 'HEADER_ONLY')]:
        reply=client.post('/api/intake',json=dict(data,stock=raw))
        assert (reply.status_code, reply.json['error'])==(422,expected)
