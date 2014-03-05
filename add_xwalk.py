from app import db, Candidate, Officer

def add_xwalk(data):
    for name, ids in data.items():
        offices = []
        for o in ids['officer_ids']:
            offices.append(Officer.query.get(o))
        cand = Candidate.query.get(ids['cand_id'])
        cand.committee_positions = offices
        db.session.add(cand)
        db.session.commit()
    return None

if __name__ == "__main__":
    import json
    data = json.load(open('candidate_officer_mapper.json', 'rb'))
    add_xwalk(data)
