from collections import Counter, defaultdict

from app.diagnostics import RampError, detail
from .reader import rows_from
from .schemas import COLUMNS, convert_fields


def channel_report(channel, raw):
    groups = defaultdict(list)
    rejected, repeated = [], []
    count, segments = 0,1
    for line,header,row in rows_from(raw,COLUMNS[channel]):
        if row==header:
            segments += 1
            continue
        count += 1
        try:
            if not any(field.strip() for field in row):
                raise ValueError('BLANK_ROW')
            if len(row)!=len(header):
                raise ValueError('WIDTH')
            data = convert_fields({key:value.strip() for key,value in zip(header,row)},channel)
            identity = (data['truck'],data['movement']) if channel=='stock' else data['ticket']
            groups[identity].append({'line':line,'data':data,'raw':row})
        except ValueError as exc:
            origin = dict(zip(header,row)) if len(row)==len(header) else {}
            rejected.append(dict(detail(str(exc)),line=line,raw=row,
                                 truck=origin.get('truck','').strip() or None))
    if not count:
        raise RampError('HEADER_ONLY')
    kept = []
    for group in groups.values():
        first,*rest = group
        if any(item['data']!=first['data'] for item in rest):
            related = [item['line'] for item in group]
            rejected.extend(dict(detail('CONFLICT'),line=r['line'],raw=r['raw'],data=r['data'],related=related)
                            for r in group)
        else:
            kept.append(first)
            repeated.extend({'line':item['line'],'kept':first['line']} for item in rest)
    return {'input':count,'accepted':len(kept),'isolated':len(rejected),'duplicate':len(repeated),'segments':segments,
            'rows':kept,'quarantine':sorted(rejected,key=lambda e:e['line']),'repeat_sources':repeated,
            'reasons':dict(Counter(row['code'] for row in rejected))}


def admit(files):
    sheets = {name:channel_report(name,files[name]) for name in COLUMNS}
    totals = {key:sum(sheet[key] for sheet in sheets.values()) for key in ('input','accepted','isolated','duplicate')}
    return dict(totals,sheets=sheets)
