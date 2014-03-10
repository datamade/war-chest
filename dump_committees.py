from app import Candidate, Report, Person
import csv
from collections import OrderedDict
from operator import itemgetter
from sqlalchemy import or_

if __name__ == "__main__":
    dump = []
    for person in Person.query.all():
        for cand in person.candidacies.all():
            for comm in cand.committees:
                c = OrderedDict()
                c['name'] = person.name
                c['committee'] = comm.name
                c['status'] = comm.status
                c['url'] = comm.url
                   #rep = Report.query.filter(Report.committee_id == comm.id)\
                   #    .filter(or_(Report.type.like('Quarterly%'), 
                   #            Report.type.like('D-2 Semiannual Report%')))\
                   #    .order_by(Report.date_filed.desc()).first()
                   #if rep:
                   #    c['current_funds'] = rep.funds_end
                   #    c['invest_total'] = rep.invest_total
                   #    c['total_assets'] = rep.funds_end + rep.invest_total
                   #else:
                   #    c['current_funds'] = None
                   #    c['invest_total'] = None
                   #    c['total_assets'] = None
                if c not in dump:
                    dump.append(c)
        for comm in person.committee_positions.all():
            if 'chair' in comm.title.lower()\
                and comm.committee.type\
                and  not comm.committee.type.lower() == 'candidate':
                c = OrderedDict()
                c['name'] = person.name
                c['committee'] = comm.committee.name
                c['status'] = comm.committee.status
                c['url'] = comm.committee.url
               #rep = Report.query.filter(Report.committee_id == comm.committee.id)\
               #    .filter(or_(Report.type.like('Quarterly%'), 
               #            Report.type.like('D-2 Semiannual Report%')))\
               #    .order_by(Report.date_filed.desc()).first()
               #if rep:
               #    c['current_funds'] = rep.funds_end
               #    c['invest_total'] = rep.invest_total
               #    c['total_assets'] = rep.funds_end + rep.invest_total
               #else:
               #    c['current_funds'] = None
               #    c['invest_total'] = None
               #    c['total_assets'] = None
                if c not in dump:
                    dump.append(c)
    dump = sorted(dump, key=itemgetter('name'))
    out = open('candidate_committees.csv', 'wb')
    outp = csv.DictWriter(out, fieldnames=dump[0].keys())
    outp.writeheader()
    outp.writerows(dump)
    out.close()
        
