from app import db, Candidate, Committee, ElectionResult
import json

def get_or_create(model, **kwargs):
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance, True

def saveit(alderman):
    cand_data = {
        'address': alderman['Address'],
        'id': alderman['Candidate ID'],
        'name': alderman['Name'],
        'party': alderman['Party'],
        'url': alderman['url']
    }
    cand = Candidate(**cand_data)
    db.session.add(cand)
    db.session.commit()
    for committee in alderman['committees']:
        comm_data = {
            'id': committee['Committee ID'],
            'name': committee['Committee Name'],
            'address': committee['Address'],
            'local_id': committee.get('Local ID'),
            'state_id': committee.get('State ID'),
            'status': committee['Status'],
            'url': committee['url'],
        }
        comm, created = get_or_create(Committee, **comm_data)
        comm.candidate = cand
        db.session.add(comm)
        db.session.commit()
    for result in alderman['results']:
        res_data = {
            'type': result['Election Type'],
            'year': result['Election Year'],
            'fair_campaign': result['Fair Campaign'],
            'cand_status': result['Inc/Chall/Open'],
            'result': result['Result'],
            'candidate': cand
        }
        res = ElectionResult(**res_data)
        db.session.add(res)
        db.session.commit()
    return None

if __name__ == '__main__':
    db.create_all()
    candidates = json.loads(open('candidates.json').read())
    aldermen = [c for c in candidates if 'Alderman/Chicago' in c['Office']]
    for alderman in aldermen:
        saveit(alderman)
