from flask import request
from app.configuration import SAMPLE_PATH
from app.diagnostics import RampError
from app.intake.schemas import COLUMNS


def sample_set(name):
    if name not in ('clean','dirty'):
        raise RampError('SAMPLE',404)
    return {key:(SAMPLE_PATH/f'{name}-{key}.csv').read_bytes() for key in COLUMNS}


def submitted():
    if request.method=='GET':
        return sample_set(request.args.get('sample','dirty'))
    body = request.get_json(silent=True)
    if isinstance(body,dict) and set(body)=={'sample'} and isinstance(body['sample'],str):
        return sample_set(body['sample'])
    if not (isinstance(body,dict) and body.keys()==COLUMNS.keys() and all(isinstance(v,str) for v in body.values())):
        raise RampError('BUNDLE')
    try:
        return {key:value.encode() for key,value in body.items()}
    except UnicodeEncodeError as exc:
        raise RampError('FILE') from exc


def bundle_from(body):
    if not body:
        return sample_set('dirty')
    if set(body)=={'sample'} and isinstance(body['sample'],str):
        return sample_set(body['sample'])
    if set(body)==set(COLUMNS) and all(isinstance(value,str) for value in body.values()):
        try:
            return {key:value.encode() for key,value in body.items()}
        except UnicodeEncodeError as exc:
            raise RampError('FILE') from exc
    raise RampError('BUNDLE')


def evidence_bundle():
    if request.method=='GET':
        return sample_set(request.args.get('sample','dirty'))
    return bundle_from(request.get_json(silent=True))


def return_submission():
    body = request.get_json(silent=True)
    orders = body.get('returns') if isinstance(body,dict) else None
    if not isinstance(orders,list) or not orders:
        raise RampError('RETURN_FIELDS')
    return bundle_from({key:value for key,value in body.items() if key!='returns'}),orders
