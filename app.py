from flask import Flask, request, make_response
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import not_, or_
import os
from datetime import date, datetime, timedelta
import json
import requests
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
CONN_STRING = 'sqlite:///war_chest.db'
app.config['SQLALCHEMY_DATABASE_URI'] = CONN_STRING

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

cand_comm = db.Table('cand_comm',
   db.Column('candidate_id', db.Integer, db.ForeignKey('candidate.id')),
   db.Column('committee_id', db.Integer, db.ForeignKey('committee.id')),
)

class Candidate(db.Model):
    __tablename__ = 'candidate'
    id = db.Column(db.Integer, primary_key=True)
    pupa_id = db.Column(db.String(255), index=True)
    name = db.Column(db.String(255), index=True)
    address = db.Column(db.String(255), index=True)
    party = db.Column(db.String(15), index=True)
    url = db.Column(db.String(255))
    office = db.Column(db.String(255), index=True)
    committee_positions = db.relationship('Officer', backref='candidate', lazy='dynamic')
    current_office_holder = db.Column(db.Boolean, default=False)
    committees = db.relationship('Committee', backref=db.backref('candidates',lazy='dynamic'), secondary=lambda: cand_comm)
    election_results = db.relationship('ElectionResult', backref='candidate', lazy='dynamic')

    def __repr__(self):
        return '<Candidate %r>' % self.name

    def as_dict(self):
        return dict([(c.name, getattr(self, c.name))
                     for c in self.__table__.columns])

class Officer(db.Model):
    __tablename__ = 'officer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    title = db.Column(db.String)
    address = db.Column(db.String)
    committee_id = db.Column(db.Integer, db.ForeignKey('committee.id'), index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), index=True)

    def __repr__(self):
        return '<Officer %r>' % self.name
    
    def as_dict(self):
        return dict([(c.name, getattr(self, c.name))
                     for c in self.__table__.columns])

class Committee(db.Model):
    __tablename__ = 'committee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)
    address = db.Column(db.String(255), index=True)
    local_id = db.Column(db.Integer, index=True)
    state_id = db.Column(db.Integer, index=True)
    status = db.Column(db.String(15), index=True)
    type = db.Column(db.String(25), index=True)
    url = db.Column(db.String(255))
    reports = db.relationship('Report', backref='committee', lazy='dynamic')
    officers = db.relationship('Officer', backref='committee', lazy='dynamic')

    def __repr__(self):
        return '<Committee %r>' % self.name

    def as_dict(self):
        return dict([(c.name, getattr(self, c.name))
                     for c in self.__table__.columns])

class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), index=True)
    period_from = db.Column(db.Date, index=True)
    period_to = db.Column(db.Date, index=True)
    date_filed = db.Column(db.DateTime, index=True)
    funds_start = db.Column(db.Float)
    funds_end = db.Column(db.Float)
    receipts = db.Column(db.Float)
    expenditures = db.Column(db.Float)
    detail_url = db.Column(db.String(255))
    committee_id = db.Column(db.Integer, db.ForeignKey('committee.id'), index=True)

    def __repr__(self):
        return '<Report %r>' % self.type

    def as_dict(self):
        return dict([(c.name, getattr(self, c.name))
                     for c in self.__table__.columns])

class ElectionResult(db.Model):
    __tablename__ = 'election_result'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), index=True)
    year = db.Column(db.Integer, index=True)
    fair_campaign = db.Column(db.String(50), index=True)
    cand_status = db.Column(db.String(15), index=True)
    result = db.Column(db.String(10), index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), index=True)

    def __repr__(self):
        return '<ElectionResult %r %r>' % (self.type, self.year)

    def as_dict(self):
        return dict([(c.name, getattr(self, c.name))
                     for c in self.__table__.columns])

dhandler = lambda obj: obj.isoformat() if isinstance(obj, date) or isinstance(obj, datetime) else None

@app.route('/war-chest/')
def war_chest():
    cands = Candidate.query.filter(Candidate.current_office_holder == True).all()
    out = []
    year_ago = datetime.now() - timedelta(days=365)
    for cand in cands:
        data = {}
        data['candidate'] = cand.name
        data['pupa_id'] = cand.pupa_id
        data['active_committees'] = []
        data['inactive_committees'] = []
        for committee in cand.committees:
            comm = {'name': committee.name}
            comm['committee_url'] = committee.url
            last_q = " ".join('select sum(receipts), sum(expenditures) from \
                report, \
                (select replace(report.type, " (Amendment)", "") as type, \
                period_from, period_to, committee_id, \
                max(date_filed) as date_filed from report where \
                committee_id = :comm_id and \
                (type like "D-2 Semiannual Report%" or type like \
                 "Quarterly%") group by replace(type, " (Amendment)", ""), \
                period_from, period_to) AS M \
                where replace(report.type, " (Amendment)", "")=M.type \
                AND report.period_from = M.period_from \
                AND report.period_to = M.period_to \
                AND report.date_filed=M.date_filed \
                AND report.committee_id=M.committee_id \
                AND report.period_from >= :per_from and report.period_to <= \
                :per_to;'.split())
            current_q = " ".join('select sum(receipts), sum(expenditures) from \
                report, \
                (select replace(report.type, " (Amendment)", "") as type, \
                period_from, period_to, committee_id, \
                max(date_filed) as date_filed from report where \
                committee_id = :comm_id and \
                (type like "D-2 Semiannual Report%" or type like \
                 "Quarterly%") group by replace(type, " (Amendment)", ""), \
                period_from, period_to) AS M \
                where replace(report.type, " (Amendment)", "")=M.type \
                AND report.period_from = M.period_from \
                AND report.period_to = M.period_to \
                AND report.date_filed=M.date_filed \
                AND report.committee_id=M.committee_id \
                AND report.period_from >= :per_from;'.split())
            latest_report = db.session.query(Report)\
                .filter(Report.committee_id == committee.id)\
                .filter(or_(Report.type.like('Quarterly%'), \
                            Report.type.like('D-2 Semiannual Report%')))\
                .order_by(Report.date_filed.desc()).first()
            last_cycle_rec, last_cycle_exp = [r for r in 
                db.engine.execute(last_q,
                comm_id=committee.id, 
                per_to='2011-06-30',
                per_from='2007-07-01')][0]
            current_cycle_rec, current_cycle_exp = [r for r in 
                db.engine.execute(current_q,
                comm_id=committee.id, 
                per_from='2011-07-01')][0]

            # have to do this because there are some blank committee pages
            if latest_report:
                comm['current_funds'] = latest_report.funds_end
                if last_cycle_rec:
                    comm['last_cycle_receipts'] = '%.2f' % last_cycle_rec
                else:
                    comm['last_cycle_receipts'] = None
                if last_cycle_exp:
                    comm['last_cycle_expenditures'] = '%.2f' % last_cycle_exp
                else:
                    comm['last_cycle_expenditures'] = None
                if current_cycle_rec:
                    comm['current_cycle_receipts'] = '%.2f' % current_cycle_rec
                else:
                    comm['current_cycle_receipts'] = None
                if current_cycle_exp:
                    comm['current_cycle_expenditures'] = '%.2f' % current_cycle_exp
                else:
                    comm['current_cycle_expenditures'] = None
                comm['latest_report_url'] = latest_report.detail_url
                comm['date_filed'] = latest_report.date_filed
                comm['reporting_period_end'] = latest_report.period_to
                comm['reporting_period_begin'] = latest_report.period_from
                if committee.status == 'Active':
                    data['active_committees'].append(comm)
                else:
                    data['inactive_committees'].append(comm)
        out.append(data)
    resp = make_response(json.dumps(out, default=dhandler))
    resp.headers['Content-Type'] = 'application/json'
    return resp

if __name__ == "__main__":
    manager.run()
