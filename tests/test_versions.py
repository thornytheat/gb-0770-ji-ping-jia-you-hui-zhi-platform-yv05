from app.meters.catalog import fleet
from app.meters.select import select_versions


def case(dirty, ticket):
    return next(row for row in dirty['versions']['rows'] if row['ticket']==ticket)


def test_overlap_higher_version_selected(dirty):  # TRAP-25
    assert case(dirty,'T07')['opened_candidates']==['F12-1','F12-2']
    assert case(dirty,'T07')['version']['id']=='F12-2'
    assert case(dirty,'S02')['fault']['code']=='VERSION_TIE'


def test_expiry_is_right_open(dirty):  # TRAP-23
    assert case(dirty,'S03')['opened_candidates']==['F18-A']
    assert case(dirty,'S03')['version']['range_l']=='500'


def test_exact_end_crosses_calibration(dirty):
    t=case(dirty,'T06')
    assert t['fault']['code']=='VERSION_SPLIT' and t['touched']==['F12-1','F12-2']


def test_boundary_crossing_inside_ticket_detected_after_return(dirty):
    ticket=dict(case(dirty,'S01')['ticket_record'],closed='2026-11-22T03:10:00.000000+00:00')
    result=select_versions([{'line':10,'data':ticket}],fleet()[0]['ranges'])
    assert result['rows'][0]['fault']['code']=='VERSION_SPLIT'


def test_version_precedes_configuration_order(dirty):
    tickets=dirty['intake']['sheets']['tickets']['rows']
    assert select_versions(tickets,list(reversed(fleet()[0]['ranges'])))==dirty['versions']


def test_unknown_truck_holds_ticket(dirty):
    ticket=dict(case(dirty,'T01')['ticket_record'],truck='UNASSIGNED')
    assert select_versions([{'line':20,'data':ticket}],fleet()[0]['ranges'])['rows'][0]['fault']['code']=='NO_VERSION'
