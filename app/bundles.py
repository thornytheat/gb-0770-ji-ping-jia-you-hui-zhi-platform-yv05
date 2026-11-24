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
