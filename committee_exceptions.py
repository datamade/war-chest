from app import db, Candidate, Committee, Report

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
    # Add proco Joe committee
    joe = Candidate.query.get(24885)
    first = Committee.query.get(24042)
    joe.committees.append(first)
    db.session.add(joe)
    
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
    
    # Add Carrie Austin Friends of 34th ward org
    carrie = Candidate.query.get(9448)
    friends = Committee.query.get(11885)
    carrie.committees.append(friends)
    db.session.add(carrie)
    
    # Add Cardenas 12th ward book comm
    cardenas = Candidate.query.get(18060)
    book_comm = Committee.query.get(21647)
    cardenas.committees.append(book_comm)
    db.session.add(cardenas)
    
    # Add Sawyer 6th ward org
    sawyer = Candidate.query.get(25044)
    sixth = Committee.query.get(24149)
    sawyer.committees.append(sixth)
    db.session.add(sawyer)
    db.session.commit()
    return None

def remove_exceptions():
    latasha = Candidate.query.get(15655)
    terry_comm = Committee.query.get(12367)
    for office in latasha.committee_positions:
        if office.committee == terry_comm:
            latasha.committee_positions.remove(office)
    pat = Candidate.query.get(2649)
    judge_comm = Committee.query.get(23699)
    for office in pat.committee_positions:
        if office.committee == judge_comm:
            pat.committee_positions.remove(office)
    tom = Candidate.query.get(17880)
    quig_comm = Committee.query.get(6301)
    for office in tom.committee_positions:
        if office.committee == quig_comm:
            tom.committee_positions.remove(office)
    scott = Candidate.query.get(21073)
    ricardo = Candidate.query.get(7187)
    reform_comm = Committee.query.get(23767)
    for office in scott.committee_positions:
        if office.committee == reform_comm:
            scott.committee_positions.remove(office)
    for office in ricardo.committee_positions:
        if office.committee == reform_comm:
            ricardo.committee_positions.remove(office)
    michelle = Candidate.query.get(21169)
    evans_comm = Committee.query.get(24362)
    for office in michelle.committee_positions:
        if office.committee == evans_comm:
            michelle.committee_positions.remove(office)
    db.session.add_all([latasha, pat, tom, scott, ricardo, michelle])
    db.session.commit()
    return None

if __name__ == "__main__":
    add_pdf_reports()
    add_exceptions()
    remove_exceptions()
