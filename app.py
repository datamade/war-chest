from flask import Flask, request, make_response
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import func
import os
from datetime import date

app = Flask(__name__)
CONN_STRING = os.environ['WARCHEST_CONN']
app.config['SQLALCHEMY_DATABASE_URI'] = CONN_STRING

db = SQLAlchemy(app)

class Candidate(db.Model):
    __tablename__ = 'candidate'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)
    address = db.Column(db.String(255), index=True)
    party = db.Column(db.String(15), index=True)
    url = db.Column(db.String(255))
    committees = db.relationship('Committee', backref='candidate', lazy='dynamic')
    election_results = db.relationship('ElectionResult', backref='candidate', lazy='dynamic')

    def __repr__(self):
        return '<Candidate %r>' % self.name

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Committee(db.Model):
    __tablename__ = 'committee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)
    address = db.Column(db.String(255), index=True)
    local_id = db.Column(db.Integer, index=True)
    state_id = db.Column(db.Integer, index=True)
    status = db.Column(db.String(15), index=True)
    url = db.Column(db.String(255))
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), index=True)
    reports = db.relationship('Report', backref='committee', lazy='dynamic')

    def __repr__(self):
        return '<Committee %r>' % self.name

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), index=True)
    period_from = db.Column(db.Date, index=True)
    period_to = db.Column(db.Date, index=True)
    funds_start = db.Column(db.Float)
    funds_end = db.Column(db.Float)
    receipts = db.Column(db.Float)
    expenditures = db.Column(db.Float)
    committee_id = db.Column(db.Integer, db.ForeignKey('committee.id'), index=True)

    def __repr__(self):
        return '<Report %r>' % self.type

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

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
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

if __name__ == "__main__":
    app.run(debug=True, port=9999)
