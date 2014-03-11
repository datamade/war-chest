from app import Person, db
import csv
from operator import itemgetter
from collections import OrderedDict

if __name__ == "__main__":
    dump = []
    for person in Person.query.all():
        for cand in person.candidacies.all():
            d = OrderedDict()
            d['person_name'] = person.name,
            d['person_id'] = person.id,
            d['officer_name'] = ''
            d['officer_id'] = ''
            d['candidate_name'] = cand.name
            d['candidate_id'] = cand.id
            if d not in dump:
                dump.append(d)
        for officer in person.committee_positions.all():
            d = OrderedDict()
            d['person_name'] = person.name,
            d['person_id'] = person.id,
            d['candidate_name'] = ''
            d['candidate_id'] = ''
            d['officer_name'] = officer.name
            d['officer_id'] = officer.id
            if d not in dump:
                dump.append(d)
    outp = open('person_candidate_mapping.csv', 'wb')
    dump = sorted(dump, key=itemgetter('person_name'))
    writer = csv.DictWriter(outp, fieldnames=dump[0].keys())
    writer.writeheader()
    writer.writerows(dump)
    outp.close()
