from concurrent.futures import ThreadPoolExecutor
import sqlite3
import pytest
from app.bundles import sample_set
from app.ledger.replay import replay,list_shifts
from app.main import create_app


def test_repeat_reuses_original_batch(client):
    first=client.post('/api/shifts',json={'sample':'dirty'})
    repeat=client.post('/api/shifts',json={'sample':'dirty'})
    assert (first.status_code, repeat.status_code)==(201,200)
    assert repeat.json==dict(first.json,reused=True)


def test_restart_reopens_all_phases(ramp,client):
    path='/api/shifts/'+client.post('/api/shifts',json={'sample':'dirty'}).json['batch']
    found=create_app(ramp.book.path).test_client().get(path).json
    assert found==client.get(path).json and len(found['stages'])==5


def test_partial_insert_rolls_back_entire_batch(ramp):
    with ramp.book.connection() as db:
        db.execute("CREATE TRIGGER fail BEFORE INSERT ON stage_rows WHEN new.phase='mass' BEGIN SELECT RAISE(ABORT,'fault'); END")
    with pytest.raises(sqlite3.IntegrityError):
        replay(ramp.book,sample_set('dirty'))
    assert list_shifts(ramp.book)==[]
    with ramp.book.connection() as db:
        assert db.execute('SELECT count(*) FROM stage_rows').fetchone()[0]==0


def test_concurrent_replay_commits_one_batch(ramp):
    with ThreadPoolExecutor(5) as pool:
        results=list(pool.map(lambda _:replay(ramp.book,sample_set('dirty')),range(7)))
    assert sum(not row['reused'] for row in results)==1
    assert len(list_shifts(ramp.book))==1


def test_replacement_receipt_is_new_batch(client):
    original=client.post('/api/shifts',json={'sample':'clean'}).json
    replacement={name:raw.decode() for name,raw in sample_set('clean').items()}
    replacement['receipts']=replacement['receipts'].replace('80.4','80')
    changed=client.post('/api/shifts',json=replacement).json
    assert original['batch']!=changed['batch'] and original['totals']==changed['totals']
    assert original['input_sha256']['tickets']==changed['input_sha256']['tickets']


def test_incomplete_submission_cannot_save(client):
    assert client.post('/api/shifts',json={'sample':'missing'}).status_code==404
    assert client.get('/api/shifts').json=={'shifts':[]}
