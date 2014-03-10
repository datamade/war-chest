from app import db, Candidate, Officer
import csv
from collections import OrderedDict
from operator import itemgetter

if __name__ == "__main__":
    names = [c.name for c in Candidate.query.filter(Candidate.current_office_holder == True).all()]
    suffixes = ['Jr', 'II', 'III']
    cand_match_table = []
    officer_match_table = []
    for name in names:
        # Try to get last name
        last_name = name.split(' ')[-1]
        first_name = name.split(' ')[0]
        if last_name in suffixes:
            last_name = name.split(' ')[-2]
        cand_matches = Candidate.query\
            .filter(Candidate.name.like('%%%s%%' % last_name))\
            .filter(Candidate.name.like('%s%%' % first_name)).all()
        for match in cand_matches:
            d = OrderedDict()
            if match.name == 'Michael J Zalewski' or match.name == 'Michael John Zalewski':
                continue
            d['query'] = '%s %s' % (first_name, last_name)
            d['candidate_name_match'] = match.name
            d['candidate_office'] = match.office
            d['candidate_url'] = match.url
            if d not in cand_matches:
                cand_match_table.append(d)
        off_matches = Officer.query\
            .filter(Officer.name.like('%%%s%%' % last_name))\
            .filter(Officer.name.like('%s%%' % first_name)).all()
        for match in off_matches:
            d = OrderedDict()
            if match.name == 'Michael J Zalewski' or match.name == 'Michael John Zalewski':
                continue
            d['query'] = '%s %s' % (first_name, last_name)
            d['officer_name_match'] = match.name
            d['officer_title'] = match.title
            d['committee_url'] = match.committee.url
            if d not in off_matches:
                officer_match_table.append(d)
    cand_match_table = sorted(cand_match_table, key=itemgetter('query'))
    officer_match_table = sorted(officer_match_table, key=itemgetter('query'))
    outp = open('candidate_name_matches.csv', 'wb')
    writer = csv.DictWriter(outp, fieldnames=cand_match_table[0].keys())
    writer.writeheader()
    writer.writerows(cand_match_table)
    outp.close()

    outp = open('officer_name_matches.csv', 'wb')
    writer = csv.DictWriter(outp, fieldnames=officer_match_table[0].keys())
    writer.writeheader()
    writer.writerows(officer_match_table)
    outp.close()
