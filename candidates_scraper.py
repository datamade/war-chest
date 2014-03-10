import requests
from app import db, Candidate, Committee
from urllib import urlencode
from urlparse import urlparse, parse_qs
import lxml.html
import time

class CandidateScraper(object):
    def __init__(self, base_url, params):
        self.base_url = base_url
        self.params = params
        self.session = requests.Session()

    def lxmlize(self, url, payload=None):
        if payload :
            entry = self.session.post(url, 'POST', payload)
        else :
            entry = self.session.get(url)
        if entry.status_code is 200:
            page = lxml.html.fromstring(entry.content)
            page.make_links_absolute(url)
        else:
            page = None
        return page

    def scrape_candidates(self):
        for page in self._grok_pages():
            if page is not None:
                table_rows = page.xpath('//tr[starts-with(@class, "SearchListTableRow")]')
                for row in table_rows:
                    data = {}
                    data['name'] = ' '.join(row.find('td[@headers="ctl00_ContentPlaceHolder1_thCandidateName"]/').xpath('.//text()'))
                    data['url'] = row.find('td[@headers="ctl00_ContentPlaceHolder1_thCandidateName"]/a').attrib['href']
                    data['address'] = ' '.join(row.find('td[@headers="ctl00_ContentPlaceHolder1_thCandidateAddress"]/').xpath('.//text()'))
                    data['party'] = ' '.join(row.find('td[@headers="ctl00_ContentPlaceHolder1_thParty"]/').xpath('.//text()'))
                    data['office'] = ' '.join(row.find('td[@headers="ctl00_ContentPlaceHolder1_thOffice"]/').xpath('.//text()'))
                    parsed = urlparse(data['url'])
                    data['id'] = parse_qs(parsed.query)['ID'][0]
                    committees = []
                    for committee in self.scrape_committees(data['url']):
                        if committee is not None:
                            committees.append(committee)
                    yield data, committees
            else:
                yield None, None

    def scrape_committees(self, url):
        page = self.lxmlize(url)
        if page is not None:
            table = page.xpath('//table[@id="ctl00_ContentPlaceHolder1_tblCommitteeInformation"]')[0]
            table_rows = table.xpath('tr[starts-with(@class, "SearchListTableRow")]')
            if table is not None:
                for row in table_rows:
                    data = {}
                    data['name'] = ' '.join(row.find('td[@class="tdCandDetailCommitteeName"]/').xpath('.//text()'))
                    data['url'] = row.find('td[@class="tdCandDetailCommitteeName"]/a').attrib['href']
                    data['address'] = ' '.join(row.find('td[@class="tdCandDetailCommitteeAddress"]/').xpath('.//text()'))
                    data['status'] = ' '.join(row.find('td[@class="tdCandDetailCommitteeStatus"]/').xpath('.//text()'))
                    ids = row.find('td[@class="tdCandDetailCommitteeID"]/').xpath('.//text()')
                    for i in ids:
                        if 'State' in i:
                            data['state_id'] = i.split(' ')[1]
                        elif 'Local' in i:
                            data['local_id'] = i.split(' ')[1]
                    parsed = urlparse(data['url'])
                    data['id'] = parse_qs(parsed.query)['id'][0]
                    detail = self.lxmlize(data['url'])
                    type = detail.xpath('//span[@id="ctl00_ContentPlaceHolder1_lblTypeOfCommittee"]')
                    if type:
                        data['type'] = detail[0].text
                    yield data
            else:
                yield None
        else:
            yield None

    def _grok_pages(self):
        query_string = urlencode(self.params)
        url = '%s?%s' % (self.base_url, query_string)
        page = self.lxmlize(url)
        page_counter = page.xpath("//span[@id='ctl00_ContentPlaceHolder1_lbRecordsInfo']")[0].text
        if page_counter:
            page_count = (int(page_counter.split(' ')[-1]) / 10)
            for page_num in range(page_count):
                self.params['pageindex'] = page_num
                qs = urlencode(self.params)
                url = '%s?%s' % (self.base_url, qs)
                yield self.lxmlize(url)
        else:
            yield page

if __name__ == "__main__":
    from app import db, Committee
    base_url = 'http://www.elections.state.il.us/CampaignDisclosure/CandidateSearch.aspx'
    params = {
        'chkFairCampNo': 'False',
        'chkFairCampYes': 'False',
        'ddlAddressSearchType': 'Starts with',
        'ddlCanDistrictType': 'All Types',
        'ddlCanElectType': 'All Types',
        'ddlCanOffice': 'All Offices',
        'ddlCanParty': 'All Parties',
        'ddlCitySearchType': 'Starts with',
        'ddlFirstNameSearchType': 'Starts with',
        'ddlLastNameSearchType': 'Starts with',
        'ddlOrderBy': 'Last Name - Z to A',
        'txtCity': 'Chicago',
    }
    scraper = CandidateScraper(base_url, params)
    for candidate, committees in scraper.scrape_candidates():
        # Save to DB and maybe write as JSON?
        if candidate is not None:
            cand = db.session.query(Candidate).get(int(candidate['id']))
            if cand:
                for k,v in candidate.items():
                    setattr(cand, k, v)
            else:
                cand = Candidate(**candidate)
            for committee in committees:
                comm = db.session.query(Committee).get(int(committee['id']))
                if comm:
                    for k,v in committee.items():
                        setattr(comm, k, v)
                    db.session.add(comm)
                    db.session.commit()
                else:
                    comm = Committee(**committee)
                    db.session.add(comm)
                    db.session.commit()
                cand.committees.append(comm)
            db.session.add(cand)
            db.session.commit()
            print cand, cand.committees
