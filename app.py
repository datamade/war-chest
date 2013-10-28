from flask import Flask, request, make_response
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import not_
import os
from datetime import date, datetime, timedelta
import json

app = Flask(__name__)
# CONN_STRING = os.environ['WARCHEST_CONN']
CONN_STRING = 'sqlite:///war_chest.db'
app.config['SQLALCHEMY_DATABASE_URI'] = CONN_STRING

db = SQLAlchemy(app)

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
    current_office_holder = db.Column(db.Boolean, default=False)
    committees = db.relationship('Committee', backref=db.backref('candidates',lazy='dynamic'), secondary=lambda: cand_comm)
    election_results = db.relationship('ElectionResult', backref='candidate', lazy='dynamic')

    def __repr__(self):
        return '<Candidate %r>' % self.name

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
    url = db.Column(db.String(255))
    reports = db.relationship('Report', backref='committee', lazy='dynamic')

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
        for committee in cand.committees:
            comm = {'name': committee.name}
            comm['committee_url'] = committee.url
            latest_report = committee.reports\
                .filter(Report.date_filed >= year_ago)\
                .order_by(Report.period_from.desc()).first()
            # have to do this because there are some blank committee pages
            if latest_report:
                comm['current_funds'] = latest_report.funds_end
                comm['last_cycle_receipts'] = latest_report.receipts
                comm['last_cycle_expenditures'] = latest_report.expenditures
                comm['latest_report_url'] = latest_report.detail_url
                comm['date_filed'] = latest_report.date_filed
                comm['reporting_period_end'] = latest_report.period_to
                data['active_committees'].append(comm)
        out.append(data)
    resp = make_response(json.dumps(out, default=dhandler))
    resp.headers['Content-Type'] = 'application/json'
    return resp

if __name__ == "__main__":
    app.run(debug=True, port=9999)
