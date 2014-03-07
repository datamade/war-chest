from app import Candidate
import csv
from collections import OrderedDict

if __name__ == "__main__":
    dump = []
    for cand in Candidate.query.filter(Candidate.current_office_holder == True).all():
        for comm in cand.committees:
            if comm.status == 'Active':
                c = OrderedDict()
                c['name'] = cand.name
                c['committee'] = comm.name
                c['url'] = comm.url
                dump.append(c)
        for comm in cand.committee_positions:
            if comm.committee.status == 'Active':
                c = OrderedDict()
                c['name'] = cand.name
                c['committee'] = comm.committee.name
                c['url'] = comm.committee.url
                dump.append(c)
    out = open('dump.csv', 'wb')
    outp = csv.DictWriter(out, fieldnames=dump[0].keys())
    outp.writeheader()
    outp.writerows(dump)
    out.close()
        
