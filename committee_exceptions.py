from app import db, Candidate, Committee, Report, Person

def add_pdf_reports():
    the_7th = Report.query.get(522550)
    the_7th.funds_start = 40.05
    the_7th.receipts = 0.0
    the_7th.expenditures = 29.97
    the_7th.invest_total = 0.0
    the_7th.funds_end = 10.08
    db.session.add(the_7th)
    db.session.commit()

def add_exceptions():
    # Add Emma Mitts committee
    emma = Candidate.query.get(15421)
    new_37 = Committee.query.get(18118)
    emma.committees.append(new_37)
    db.session.add(emma)

    # Add Roberto Maldonado committee
    robert = Candidate.query.get(23923)
    the_26 = Committee.query.get(15492)
    robert.committees.append(the_26)
    db.session.add(robert)

    # Add Bob Fioretti committee
    bob = Candidate.query.get(25571)
    second = Committee.query.get(23191)
    bob.committees.append(second)
    db.session.add(bob)

    # Add Latasha Thomas 17th ward org
    latasha = Candidate.query.get(15655)
    seventeenth = Committee.query.get(16229)
    latasha.committees.append(seventeenth)
    
    # Add Laurino 39th ward org
    laurino = Candidate.query.get(7853)
    thirty = Committee.query.get(11463)
    laurino.committees.append(thirty)
    db.session.add(laurino)
    
    db.session.commit()
    return None

def remove_exceptions():
    ricardo = Person.query.filter(Person.name == 'Ricardo Munoz').first()
    reform_comm = Committee.query.get(23767)
    positions = ricardo.committee_positions.all()
    for off in positions:
        if off.committee == reform_comm:
            positions.remove(off)
    ricardo.committee_positions = positions
    db.session.add(ricardo)
    db.session.commit()

if __name__ == "__main__":
    add_pdf_reports()
    add_exceptions()
    remove_exceptions()
