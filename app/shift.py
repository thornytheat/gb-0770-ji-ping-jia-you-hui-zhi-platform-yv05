from app.conversion.calculate import weigh
from app.intake.evidence import admit
from app.meters.catalog import fleet
from app.meters.select import select_versions
from app.readings.rebuild import rebuild
from app.settlement.report import reconcile


def compute(files, through='balance', catalog=None):
    stage = {'intake':admit(files)}
    if through=='intake':
        return stage
    catalog = catalog if catalog is not None else fleet()[0]
    stage['versions'] = select_versions(stage['intake']['sheets']['tickets']['rows'],catalog['ranges'])
    if through=='versions':
        return stage
    stage['readings'] = rebuild(stage['versions']['rows'])
    if through=='readings':
        return stage
    stage['mass'] = weigh(stage['readings']['rows'],catalog['fuels'])
    if through!='mass':
        stage['balance'] = reconcile(stage['mass']['rows'],stage['intake'])
    return stage
