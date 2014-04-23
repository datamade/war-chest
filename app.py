from flask import Flask, request, make_response
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.sql import not_, or_
import os
from datetime import date, datetime, timedelta
import json
import requests
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from operator import itemgetter, attrgetter
from itertools import groupby

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

class Person(db.Model):
    __tablename__ = 'person'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)
    pupa_id = db.Column(db.String(255), index=True)
    current_office_holder = db.Column(db.Boolean, default=False)
    candidacies = db.relationship('Candidate', backref='person', lazy='dynamic')
    committee_positions = db.relationship('Officer', backref='person', lazy='dynamic')
    
    def __repr__(self):
        return '<Person %r>' % self.name

class Candidate(db.Model):
    __tablename__ = 'candidate'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)
    address = db.Column(db.String(255), index=True)
    party = db.Column(db.String(15), index=True)
    url = db.Column(db.String(255))
    office = db.Column(db.String(255), index=True)
    current_office_holder = db.Column(db.Boolean, default=False)
    pupa_id = db.Column(db.String(255), index=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), index=True)
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
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), index=True)

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

    @hybrid_method
    def cycle_reports(self, start=None, end=None):
        reports = self.reports.filter(self.status != 'Final')\
            .filter(Report.period_from >= datetime.strptime(start, '%Y-%m-%d').date())\
            .filter(or_(Report.generic_type.like('Quarterly'), 
                Report.generic_type.like('D-2 Semiannual Report')))
        if end:
            reports = reports.filter(Report.period_to <= datetime.strptime(end, '%Y-%m-%d').date())
        return reports

    @hybrid_method
    def cycle_totals(self, start=None, end=None):
        reports = self.cycle_reports(start, end)\
            .order_by(Report.period_to.desc()).all()
        the_ones = []
        for k,g in groupby(reports, key=attrgetter('period_to')):
            the_ones.append(sorted(list(g), key=attrgetter('date_filed'), reverse=True)[0])
        receipts = sum(r.receipts for r in the_ones if r.receipts)
        expenditures = sum(r.expenditures for r in the_ones if r.expenditures)
        if receipts or expenditures:
            return receipts, expenditures
        else:
            return 0, 0

class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), index=True)
    generic_type = db.Column(db.String(50), index=True)
    period_from = db.Column(db.Date, index=True)
    period_to = db.Column(db.Date, index=True)
    date_filed = db.Column(db.DateTime, index=True)
    funds_start = db.Column(db.Float)
    funds_end = db.Column(db.Float)
    receipts = db.Column(db.Float)
    expenditures = db.Column(db.Float)
    invest_total = db.Column(db.Float)
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
    people = Person.query.filter(Person.pupa_id != None).all()
    year_ago = datetime.now() - timedelta(days=365)
    out = []
    for person in people:
        committees = []
        for cand in person.candidacies.all():
            for c in cand.committees:
                if c.status != 'Final' and c not in committees:
                    committees.append(c)
        for off in person.committee_positions.all():
            if 'chair' in off.title.lower()\
                and off.committee.type\
                and  not off.committee.type.lower() == 'candidate'\
                and off.committee not in committees:
                committees.append(off.committee)
        data = {}
        data['candidate'] = person.name
        data['pupa_id'] = person.pupa_id
        data['active_committees'] = []
        data['inactive_committees'] = []
        for committee in committees:
            comm = {
                'name': committee.name,
                'type': committee.type
            }
            comm['committee_url'] = committee.url
            latest_report = db.session.query(Report)\
                .filter(Report.committee_id == committee.id)\
                .filter(or_(Report.generic_type.like('Quarterly%'), \
                            Report.generic_type.like('D-2 Semiannual Report%')))\
                .order_by(Report.date_filed.desc()).first()
            last_cycle_rec, last_cycle_exp = committee.cycle_totals(start='2007-07-01', end='2011-06-30')
            current_cycle_rec, current_cycle_exp = committee.cycle_totals(start='2011-07-01')
            if latest_report:
                comm['current_funds'] = latest_report.funds_end
                comm['invest_total'] = latest_report.invest_total
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
    resp = make_response(json.dumps(out, default=dhandler, indent=4))
    resp.headers['Content-Type'] = 'application/json'
    return resp

if __name__ == "__main__":
    manager.run()
