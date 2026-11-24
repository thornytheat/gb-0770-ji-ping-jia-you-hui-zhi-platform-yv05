def compile_slip(archive):
    stages = archive['stages']
    return {'document':'机坪加注证据单','manifest':archive['manifest'],
            'conservation':stages['balance'],'counter_checks':stages['mass']['rows'],
            'sources':stages['intake']['sheets']}
