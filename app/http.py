from flask import Blueprint, current_app, jsonify
from app.bundles import submitted
from app.dispatch.signatures import evidence_file,sign
from app.ledger.replay import list_shifts,replay,shift
from app.shift import compute

routes = Blueprint('ramp_api',__name__)


def evaluate(stage):
    return compute(submitted(),stage)[stage]


@routes.route('/api/intake',methods=['GET','POST'])
def intake():
    return evaluate('intake')


@routes.route('/api/versions',methods=['GET','POST'])
def versions():
    return evaluate('versions')


@routes.route('/api/readings',methods=['GET','POST'])
def readings():
    return evaluate('readings')


@routes.route('/api/mass',methods=['GET','POST'])
def mass():
    return evaluate('mass')


@routes.route('/api/balance',methods=['GET','POST'])
def balance():
    return evaluate('balance')


@routes.get('/api/shifts')
def shifts():
    return {'shifts':list_shifts(current_app.book)}


@routes.post('/api/shifts')
def archive():
    result = replay(current_app.book,submitted())
    return result,200 if result['reused'] else 201


@routes.get('/api/shifts/<batch>')
def load(batch):
    return shift(current_app.book,batch)


@routes.post('/api/shifts/<batch>/sign')
def issue(batch):
    return sign(current_app.book,batch)


@routes.get('/api/shifts/<batch>/export')
def export(batch):
    result = jsonify(evidence_file(current_app.book,batch))
    result.headers['Content-Disposition'] = f'attachment; filename="fuel-{batch}.json"'
    return result
