from app import db, Candidate, Officer, Person
import csv
import json
from collections import OrderedDict
from operator import itemgetter
from sqlalchemy import or_

if __name__ == "__main__":
    cands = [c for c in Candidate.query.filter(Candidate.current_office_holder == True).all()]
    suffixes = ['Jr', 'II', 'III']
    match_table = []
    for cand in cands:
        # Try to get last name
        last_name = cand.name.split(' ')[-1]
        first_name = cand.name.split(' ')[0]
        if last_name in suffixes:
            last_name = cand.name.split(' ')[-2]
        cand_matches = Candidate.query\
            .filter(Candidate.name.like('%%%s%%' % last_name))\
            .filter(Candidate.name.like('%s%%' % first_name)).all()
        d = {
            'cand_id': cand.id, 
            'cand_name': cand.name,
            'cand_matches': [],
            'off_matches': [],
        }
        for match in cand_matches:
            m = {}
            if match.name == 'Michael J Zalewski'\
                or match.name == 'Michael John Zalewski'\
                or match.name == "Matthew G O'Shea"\
                or match.name == "Patrick O'Connor":
                continue
            m['match_id'] = match.id
            m['match_name'] = match.name
            m['match_url'] = match.url
            d['cand_matches'].append(m)
        off_matches = Officer.query\
            .filter(Officer.name.like('%%%s%%' % last_name))\
            .filter(Officer.name.like('%s%%' % first_name)).all()
        for match in off_matches:
            m = {}
            if match.name == 'Michael J Zalewski'\
                or match.name == 'Michael John Zalewski'\
                or match.name == "Matthew G O'Shea"\
                or match.name == "Patrick O'Connor":
                continue
            m['match_id'] = match.id
            m['match_name'] = match.name
            m['match_url'] = match.committee.url
            d['off_matches'].append(m)
        match_table.append(d)
    outp = open('candidate_name_matches.json', 'wb')
    outp.write(json.dumps(match_table, indent=4))
    outp.close()
    for cand in match_table:
        cand_records = [Candidate.query.get(cand['cand_id'])]
        off_records = []
        for c in cand['cand_matches']:
            cand_records.append(Candidate.query.get(c['match_id']))
        for o in cand['off_matches']:
            off_records.append(Officer.query.get(o['match_id']))
        person = db.session.query(Person)\
            .filter(Person.candidacies.any(Candidate.id == cand['cand_id'])).first()
        if not person:
            person = Person(
                candidacies=cand_records, 
                committee_positions=off_records,
                name=cand_records[0].name,
                current_office_holder=True,
                pupa_id=cand_records[0].pupa_id)
            db.session.add(person)
            db.session.commit()
