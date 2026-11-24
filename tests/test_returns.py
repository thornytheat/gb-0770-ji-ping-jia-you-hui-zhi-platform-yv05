from concurrent.futures import ThreadPoolExecutor

from app.bundles import sample_set
from app.returns.ledger import submit

PREV_SHIFT = {
    'tickets':('ticket,truck,opened,closed,start_l,stop_l,event,fuel,rho,rho_unit,temp_c\n'
               'P01,FT-12,2026-11-21T08:00:00Z,2026-11-21T08:10:00Z,10,110,normal,JET-A1,800,kg/m3,15\n'),
    'receipts':'ticket,truck,signed_kg,document\nP01,FT-12,80,P91\n',
    'stock':'truck,movement,kind,kg\nFT-12,O12,opening,300\nFT-12,C12,closing,220\n',
}


def order(return_id,ticket='T01',truck='FT-12',kg='10',weighbill=None):
    return {'return_id':return_id,'ticket':ticket,'truck':truck,'kg':kg,
            'weighbill':weighbill or f'WB-{return_id}'}


def post_returns(client,*orders):
    return client.post('/api/returns',json={'sample':'dirty','returns':list(orders)})


def stock_of(report,truck):
    return next(row for row in report['stocks'] if row['truck']==truck)


def test_weighed_return_enters_receiving_truck_shift_stock(client):
    response = post_returns(client,order('RT-01',truck='FT-18',kg='10'))
    assert response.status_code==201
    row = response.json['returns'][0]
    assert (row['inventory'],row['writeoff'],row['confirmed_g'])==('ENTERED','CONFIRMED',10000)
    report = client.get('/api/returns?sample=dirty').json
    truck = stock_of(report,'FT-18')
    assert truck['returned_g']==10000
    assert truck['physical_difference_g']==truck['difference_g']+10000


def test_original_ticket_from_previous_shift(client):
    assert client.post('/api/shifts',json=PREV_SHIFT).status_code==201
    response = post_returns(client,order('RT-02',ticket='P01',truck='FT-18',kg='10'))
    row = response.json['returns'][0]
    assert row['writeoff']=='CONFIRMED'
    assert row['evidence']=={'ticket_found':True,'signed_g':80000,'remaining_g':70000}


def test_writeoff_capped_at_signed_amount(client):
    row = post_returns(client,order('RT-03',kg='80.4')).json['returns'][0]
    assert (row['writeoff'],row['confirmed_g'])==('CONFIRMED',80400)
    assert row['evidence']['remaining_g']==0


def test_single_overlimit_return_fully_pending(client):
    row = post_returns(client,order('RT-04',kg='90')).json['returns'][0]
    assert (row['writeoff'],row['confirmed_g'])==('PENDING',0)
    assert row['reason']['code']=='OVER_REMAINING'
    assert row['inventory']=='ENTERED'


def test_missing_ticket_or_receipt_pending_but_stocked(client):
    response = post_returns(client,order('RT-05',ticket='GHOST',kg='4'),order('RT-06',ticket='T04',kg='6'))
    first,second = response.json['returns']
    assert (first['writeoff'],first['reason']['code'],first['inventory'])==('PENDING','NO_TICKET','ENTERED')
    assert (second['writeoff'],second['reason']['code'],second['inventory'])==('PENDING','NO_RECEIPT','ENTERED')
    report = client.get('/api/returns?sample=dirty').json
    assert stock_of(report,'FT-12')['returned_g']==10000
    assert report['totals']=={'orders':2,'returned_g':10000,'confirmed_g':0,'pending_g':10000,'pending':2}


def test_simultaneous_pair_only_one_confirms(client):
    response = post_returns(client,order('RT-07',kg='50'),order('RT-08',kg='50'))
    first,second = response.json['returns']
    assert (first['writeoff'],first['confirmed_g'])==('CONFIRMED',50000)
    assert (second['writeoff'],second['reason']['code'])==('PENDING','OVER_REMAINING')
    assert client.get('/api/returns?sample=dirty').json['totals']['confirmed_g']==50000


def test_concurrent_submissions_confirm_only_one(ramp):
    files = sample_set('dirty')
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda o:submit(ramp.book,files,[o]),
                                [order('RT-09',kg='50'),order('RT-10',kg='50')]))
    states = [result['returns'][0]['writeoff'] for result in results]
    assert sorted(states)==['CONFIRMED','PENDING']
    from app.returns.report import returns_report
    totals = returns_report(ramp.book,files)['totals']
    assert (totals['confirmed_g'],totals['pending_g'])==(50000,50000)


def test_retry_same_return_not_duplicated(client):
    first = post_returns(client,order('RT-11'))
    assert first.status_code==201
    repeat = post_returns(client,order('RT-11'))
    assert repeat.status_code==200
    assert repeat.json=={'returns':[dict(first.json['returns'][0],reused=True)],'created':0,'reused':1}
    report = client.get('/api/returns?sample=dirty').json
    assert report['totals']=={'orders':1,'returned_g':10000,'confirmed_g':10000,'pending_g':0,'pending':0}


def test_same_number_different_content_rejected(client):
    post_returns(client,order('RT-12',kg='10'))
    response = post_returns(client,order('RT-12',kg='12'))
    assert (response.status_code,response.json['error'])==(409,'RETURN_MISMATCH')


def test_voucher_keeps_weighbill_and_writeoff_status(client):
    post_returns(client,order('RT-13',kg='10'),order('RT-14',kg='90'))
    issued = client.post('/api/returns/RT-13/voucher',json={'sample':'dirty'})
    assert issued.status_code==201
    voucher = issued.json['voucher']
    assert voucher['weighbill']=='WB-RT-13'
    assert voucher['writeoff']=={'status':'CONFIRMED','confirmed_g':10000,'reason':None}
    again = client.post('/api/returns/RT-13/voucher',json={'sample':'dirty'})
    assert (again.status_code,again.json['reused'],again.json['checksum'])==(200,True,issued.json['checksum'])
    fetched = client.get('/api/returns/RT-13/voucher').json
    assert fetched['verified'] and fetched['voucher']==voucher
    pending = client.post('/api/returns/RT-14/voucher',json={'sample':'dirty'}).json['voucher']
    assert pending['writeoff']=={'status':'PENDING','confirmed_g':0,'reason':'OVER_REMAINING'}
    assert pending['weighbill']=='WB-RT-14'


def test_review_confirms_after_evidence_arrives(client):
    row = post_returns(client,order('RT-15',ticket='P02',kg='40')).json['returns'][0]
    assert row['reason']['code']=='NO_TICKET'
    prev = dict(PREV_SHIFT)
    prev['tickets'] = prev['tickets'].replace('P01','P02')
    prev['receipts'] = prev['receipts'].replace('P01','P02').replace('80,','40,')
    assert client.post('/api/shifts',json=prev).status_code==201
    reviewed = client.post('/api/returns/RT-15/review',json={'sample':'dirty'}).json
    assert reviewed['changed'] and reviewed['writeoff']=='CONFIRMED' and reviewed['confirmed_g']==40000
    assert client.post('/api/returns/RT-15/review',json={'sample':'dirty'}).json['changed'] is False


def test_invalid_submissions_rejected(client):
    assert client.post('/api/returns',json={'sample':'dirty','returns':[]}).status_code==422
    assert post_returns(client,{'return_id':'RT-16','ticket':'T01','truck':'FT-12','kg':'10'}).status_code==422
    assert post_returns(client,order('RT-17',kg='12.3456')).json['error']=='RETURN_FIELDS'
    assert post_returns(client,order('RT-18',kg='0')).json['error']=='RETURN_FIELDS'
    assert client.post('/api/returns/RT-99/review',json={}).status_code==404
    assert client.get('/api/returns/RT-99/voucher').status_code==404
    post_returns(client,order('RT-19'))
    assert client.get('/api/returns/RT-19/voucher').json['error']=='NO_VOUCHER'


def test_returns_worktop_page(client):
    shown = client.get('/ops/returns').get_data(as_text=True)
    assert '退油对账' in shown and '磅单' in shown and '实存差额' in shown
    post_returns(client,order('RT-20',truck='FT-18',kg='7'))
    shown = client.get('/ops/returns').get_data(as_text=True)
    assert 'RT-20' in shown and 'WB-RT-20' in shown and '已冲销' in shown
