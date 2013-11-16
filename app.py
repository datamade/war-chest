from flask import Flask, request, make_response
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import not_
import os
from datetime import date, datetime, timedelta
import json
import requests

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

@app.route('/clout-details/')
def clout_details():
    # Call people endpoint and get all the people
    url = 'http://chicagoelections.datamade.us'
    people = requests.get('%s/clout/' % url)
    if people.status_code is 200:
        people_results = people.json()
        all_people = []
        for person in people_results:
            p = {
                'name': person['alderman'],
                'id': person['id'],
                'clout': person['clout'],
                'rank': person['rank'],
                'committee_chairs': [],
                'ward': [],
                'image': [], # url to image
                'tenure': [], # in years
                'war-chest': [] # in USD
            }
            person_detail = requests.get('%s/imago/%s/' % (url, person['id']))
            if person_detail.status_code is 200:
                pers = person_detail.json()
                p['image'] = pers['image']
                memberships = pers['memberships']
                for membership in memberships:
                    name = membership['organization']['name'].lower()
                    role = membership['role'].lower()
                    if not name.startswith('joint committee:') and role == 'chairman' and 'city council' not in name:
                        p['committee_chairs'].append(membership['organization']['name'])
                    elif 'city council' in name:
                        p['ward'] = int(membership['post_id'])
                        # Calculate tenure
                        p['tenure'] = date.today().year - int(membership['start_date'])
            else:
                resp = make_response(json.dumps({'status': 'error', 'message': 'Something went wrong while performing your query. Try again'}), 500)
            # Now call the /war-chest/ endpoint and get the money part
            # An alternate way would be to run the same queries as above (in the war-chest route)
            # for just the candidate that you want. I think that might actually be better....
            # Uh, OK, I gotta go pick up my kid

            print p
            all_people.append(p)
            break
        resp = make_response(json.dumps(all_people, default=dhandler))
    else: 
        resp = make_response(json.dumps({'status': 'error', 'message': 'Something went wrong while performing your query. Try again'}), 500)

    resp.headers['Content-Type'] = 'application/json'
    return resp

if __name__ == "__main__":
    app.run(debug=True, port=9999)
