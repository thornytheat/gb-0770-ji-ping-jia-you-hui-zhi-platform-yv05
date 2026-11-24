from decimal import Decimal
from flask import Blueprint,current_app,render_template,request

from app.bundles import sample_set
from app.configuration import RULESET
from app.diagnostics import RampError
from app.ledger.replay import list_shifts
from app.shift import compute

SECTIONS = {'balance':'库存和签单对账','intake':'仪表与回执采信','versions':'罐车量程配置选版','readings':'两端读数重建',
            'mass':'密度换算与误差带','shifts':'批次留档复跑','sign':'加注证据签发'}
display = Blueprint('ramp',__name__)


@display.app_template_filter('kg')
def to_kg(value):
    return f'{Decimal(value)/1000:,.3f}' if value is not None else '—'


@display.get('/')
@display.get('/ops/<tab>')
def view(tab='balance'):
    if tab not in SECTIONS:
        raise RampError('SAMPLE',404)
    name = request.args.get('sample','dirty')
    data = compute(sample_set(name),'balance')
    runs = list_shifts(current_app.book) if tab in ('shifts','sign') else []
    return render_template('base.html',section=tab,tabs=SECTIONS,sample=name,data=data,rev=RULESET,
                           runs=runs,current=request.args.get('batch',''))
