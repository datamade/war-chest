from app import db, Candidate, Committee

def add_exceptions():
    emma = Candidate.query.get(15421)
    new_37 = Committee.query.get(18118)
    emma.committees.append(new_37)
    db.session.add(emma)
    robert = Candidate.query.get(23923)
    the_26 = Committee.query.get(15492)
    robert.committees.append(the_26)
    db.session.add(robert)
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
    add_exceptions()
    remove_exceptions()
