from app import db, Candidate
import csv
from collections import OrderedDict
from operator import itemgetter

if __name__ == "__main__":
    names = [c.name for c in Candidate.query.filter(Candidate.current_office_holder == True).all()]
    suffixes = ['Jr', 'II', 'III']
    match_table = []
    for name in names:
        # Try to get last name
        last_name = name.split(' ')[-1]
        first_name = name.split(' ')[0]
        if last_name in suffixes:
            last_name = name.split(' ')[-2]
        matches = Candidate.query\
            .filter(Candidate.name.like('%%%s%%' % last_name))\
            .filter(Candidate.name.like('%s%%' % first_name)).all()
        for match in matches:
            d = OrderedDict()
            if match.name == 'Michael R Zalewski':
                continue
            d['query'] = '%s %s' % (first_name, last_name)
            d['candidate_name_match'] = match.name
            d['candidate_office'] = match.office
            d['candidate_url'] = match.url
            match_table.append(d)
    match_table = sorted(match_table, key=itemgetter('query'))
    outp = open('candidate_name_matches.csv', 'wb')
    writer = csv.DictWriter(outp, fieldnames=match_table[0].keys())
    writer.writeheader()
    writer.writerows(match_table)
    outp.close()

