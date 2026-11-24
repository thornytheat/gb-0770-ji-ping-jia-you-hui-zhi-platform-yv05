from collections import defaultdict
from app.diagnostics import detail


def candidates(ranges, at):
    return [row for row in ranges if row['since']<=at<row['until']]


def winner(options):
    if not options:
        return None,'NO_VERSION'
    highest = max(row['revision'] for row in options)
    chosen = [row for row in options if row['revision']==highest]
    return (chosen[0],None) if len(chosen)==1 else (None,'VERSION_TIE')


def select_versions(tickets, versions):
    trucks = defaultdict(list)
    for row in versions:
        trucks[row['truck']].append(row)
    rows = []
    for ticket in tickets:
        info = ticket['data']
        ranges = trucks[info['truck']]
        start,end = info['opened'],info['closed']
        first = candidates(ranges,start)
        selection,reason = winner(first)
        boundaries = sorted({row[key] for row in ranges for key in ('since','until') if start < row[key] <= end})
        touched = {row['id'] for row in first}
        for at in boundaries:
            options = candidates(ranges,at)
            candidate,_ = winner(options)
            touched.update(row['id'] for row in options)
            if selection and candidate!=selection:
                reason = 'VERSION_SPLIT'
        rows.append({'ticket':info['ticket'],'truck':info['truck'],'line':ticket['line'],'ticket_record':info,
                     'opened_candidates':sorted(row['id'] for row in first),'touched':sorted(touched),
                     'version':selection if not reason else None,'fault':detail(reason) if reason else None})
    return {'rows':rows,'selected':sum(row['fault'] is None for row in rows),
            'held':sum(row['fault'] is not None for row in rows),
            'overlaps':sum(len(row['opened_candidates'])>1 for row in rows)}
