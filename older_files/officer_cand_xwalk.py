from app import db, Candidate, Officer
import json
from sqlalchemy import or_
from operator import itemgetter
from itertools import groupby
from collections import OrderedDict

def dump_cands():
    cands = db.session.query(Candidate)\
        .filter(or_(
            Candidate.office == 'Alderman/Chicago', 
            Candidate.name == 'Deb Mell'))\
        .filter(Candidate.current_office_holder == True)\
        .all()
    cand_mapping = {}
    for cand in cands:
        cand_mapping[cand.name] = {'cand_id': cand.id, 'officer_ids': []}
    return OrderedDict(sorted(cand_mapping.iteritems(), key=itemgetter(0)))

def dump_officers():
    officers = Officer.query.all()
    data = []
    for officer in officers:
        d = [officer.name, officer.id]
        data.append(d)
    data = sorted(data, key=itemgetter(0))
    officer_mapper = {}
    for k,g in groupby(data, key=itemgetter(0)):
       officer_mapper[k] = [i[1] for i in list(g)]
    return OrderedDict(sorted(officer_mapper.iteritems(), key=itemgetter(0)))

if __name__ == "__main__":
    aldermen = dump_cands()
    officers = dump_officers()
    with open('candidate_mapper.json', 'wb') as ald_out:
        ald_out.write(json.dumps(aldermen, indent=4))
    with open('officer_mapper.json', 'wb') as off_out:
        off_out.write(json.dumps(officers, indent=4))
