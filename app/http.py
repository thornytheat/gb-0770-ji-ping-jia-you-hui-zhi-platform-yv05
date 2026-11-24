from flask import Blueprint, current_app, jsonify, request
from app.bundles import evidence_bundle, return_submission, submitted
from app.dispatch.signatures import evidence_file,sign
from app.ledger.replay import list_shifts,replay,shift
from app.returns.ledger import fetch_voucher,issue_voucher,review,submit
from app.returns.report import returns_report
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


@routes.route('/api/returns',methods=['GET','POST'])
def fuel_returns():
    if request.method=='GET':
        return returns_report(current_app.book,evidence_bundle())
    files,orders = return_submission()
    result = submit(current_app.book,files,orders)
    return result,201 if result['created'] else 200


@routes.post('/api/returns/<return_id>/review')
def fuel_return_review(return_id):
    return review(current_app.book,evidence_bundle(),return_id)


@routes.route('/api/returns/<return_id>/voucher',methods=['GET','POST'])
def fuel_return_voucher(return_id):
    if request.method=='POST':
        result = issue_voucher(current_app.book,evidence_bundle(),return_id)
        return result,200 if result['reused'] else 201
    return fetch_voucher(current_app.book,return_id)
