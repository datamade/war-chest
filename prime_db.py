from app import db, Candidate, Committee, ElectionResult
import json

def saveit(alderman):
    cand_data = {
        'address': alderman['Address'],
        'id': alderman['Candidate ID'],
        'name': alderman['Name'],
        'party': alderman['Party'],
        'url': alderman['url'],
        'office' : alderman['Office']
    }
    cand = Candidate(**cand_data)
    comms = []
    for committee in alderman['committees']:
        c = Committee.query.get(committee['Committee ID'])
        if c:
            comms.append(c)
        else:
            comm_data = {
                'id': committee['Committee ID'],
                'name': committee['Committee Name'],
                'address': committee['Address'],
                'local_id': committee.get('Local ID'),
                'state_id': committee.get('State ID'),
                'status': committee['Status'],
                'url': committee['url'],
            }
            comms.append(Committee(**comm_data))
    cand.committees = comms
    db.session.add(cand)
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
    for candidate in candidates :
        if ('Alderman/Chicago' in candidate['Office']
            or candidate['Name'] in ("Michael D Chandler", "Deb Mell")) : 
            saveit(candidate)
