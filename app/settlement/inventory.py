from collections import defaultdict
from app.diagnostics import detail


def conservation(stock, findings):
    holding = defaultdict(lambda:defaultdict(list))
    for item in stock['rows']:
        row = item['data']
        holding[row['truck']][row['kind']].append(item)
    held_positions = defaultdict(list)
    for item in stock['quarantine']:
        truck = item['data']['truck'] if 'data' in item else item.get('truck')
        if truck:
            held_positions[truck].append(item['line'])
    issued = defaultdict(int)
    for finding in findings:
        issued[finding['truck']] += finding['meter_g'] or 0
    result = []
    for truck in sorted(set(holding) | set(issued) | set(held_positions)):
        entries = holding[truck]
        opening,closing = entries['opening'],entries['closing']
        inbound = sum(row['data']['mass_g'] for row in entries['inbound'])
        issue = issued[truck]
        complete = len(opening)==len(closing)==1 and not held_positions[truck]
        start = opening[0]['data']['mass_g'] if len(opening)==1 else None
        end = closing[0]['data']['mass_g'] if len(closing)==1 else None
        residual = start+inbound-issue-end if complete else None
        result.append({'truck':truck,'opening_g':start,'inbound_g':inbound,'issued_g':issue,'closing_g':end,
                       'difference_g':residual,'complete':complete,
                       'fault':None if complete else detail('STOCK_ANCHORS'),
                       'source_lines':sorted(item['line'] for group in entries.values() for item in group),
                       'isolated_lines':held_positions[truck]})
    return result
