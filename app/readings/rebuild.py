from app.diagnostics import detail
from .delta import difference


def rebuild(selection):
    lines = []
    for record in selection:
        fault,liters = record['fault'],None
        if not fault:
            liters,reason = difference(record['ticket_record'],record['version'])
            if reason:
                fault = detail(reason)
        lines.append(dict(record,fault=fault,volume_l=format(liters,'f') if liters is not None else None,
                          method=record['ticket_record']['event'] if not fault else None))
    return {'rows':lines,'reconstructed':sum(row['fault'] is None for row in lines),
            'rollovers':sum(row['method']=='wrap' for row in lines),
            'held':sum(row['fault'] is not None for row in lines)}
