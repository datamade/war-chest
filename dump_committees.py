from app import Candidate, Report
import csv
from collections import OrderedDict
from sqlalchemy import or_

if __name__ == "__main__":
    dump = []
    for cand in Candidate.query.filter(Candidate.current_office_holder == True).all():
        for comm in cand.committees:
            if comm.status == 'Active':
                c = OrderedDict()
                c['name'] = cand.name
                c['committee'] = comm.name
                c['url'] = comm.url
                c['position'] = 'In Support of Candidate'
                rep = Report.query.filter(Report.committee_id == comm.id)\
                    .filter(or_(Report.type.like('Quarterly%'), 
                            Report.type.like('D-2 Semiannual Report%')))\
                    .order_by(Report.date_filed.desc()).first()
                if rep:
                    c['current_funds'] = rep.funds_end
                    c['invest_total'] = rep.invest_total
                    c['total_assets'] = rep.funds_end + rep.invest_total
                else:
                    c['current_funds'] = None
                    c['invest_total'] = None
                    c['total_assets'] = None
                dump.append(c)
        for comm in cand.committee_positions:
            if comm.committee.status == 'Active':
                c = OrderedDict()
                c['name'] = cand.name
                c['committee'] = comm.committee.name
                c['url'] = comm.committee.url
                c['position'] = 'Candidate is %s' % comm.title
                rep = Report.query.filter(Report.committee_id == comm.committee.id)\
                    .filter(or_(Report.type.like('Quarterly%'), 
                            Report.type.like('D-2 Semiannual Report%')))\
                    .order_by(Report.date_filed.desc()).first()
                if rep:
                    c['current_funds'] = rep.funds_end
                    c['invest_total'] = rep.invest_total
                    c['total_assets'] = rep.funds_end + rep.invest_total
                else:
                    c['current_funds'] = None
                    c['invest_total'] = None
                    c['total_assets'] = None
                dump.append(c)
    out = open('dump.csv', 'wb')
    outp = csv.DictWriter(out, fieldnames=dump[0].keys())
    outp.writeheader()
    outp.writerows(dump)
    out.close()
        
