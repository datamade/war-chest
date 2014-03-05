import requests
from app import db, Committee
from urllib import urlencode
import lxml.html

class CommitteeScraper(object):
    def __init__(self, base_url, params):
        self.base_url = base_url
        self.params = params
        self.session = requests.Session()

    def lxmlize(self, url, payload=None):
        if payload :
            entry = self.session.post(url, 'POST', payload)
        else :
            entry = self.session.get(url)
        page = lxml.html.fromstring(entry.content)
        page.make_links_absolute(url)
        return page

    def scrape_committees(self):
        for page in self._grok_pages():
            table_rows = page.xpath('//tr[starts-with(@class, "SearchListTableRow")]')
            for row in table_rows:
                data = {}
                data['name'] = ' '.join(row.find('td[@headers="thCommitteeName"]/').xpath('.//text()'))
                data['url'] = row.find('td[@headers="thCommitteeName"]/a').attrib['href']
                data['address'] = ' '.join(row.find('td[@headers="thAddress"]/').xpath('.//text()'))
                data['status'] = ' '.join(row.find('td[@headers="thStatus"]/').xpath('.//text()'))
                ids = row.find('td[@headers="thStateLocalID"]/').xpath('.//text()')
                for i in ids:
                    if 'State' in i:
                        data['state_id'] = i.split(' ')[1]
                    elif 'Local' in i:
                        data['local_id'] = i.split(' ')[1]
                data['id'] = ' '.join(row.find('td[@headers="thCommitteeID"]/').xpath('.//text()'))
                detail = self.lxmlize(data['url'])
                data['type'] = detail.xpath('//span[@id="ctl00_ContentPlaceHolder1_lblTypeOfCommittee"]')[0].text
                yield data


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
            yield None

if __name__ == "__main__":
    from app import db, Committee
    base_url = 'http://www.elections.state.il.us/CampaignDisclosure/CommitteeSearch.aspx'
    params = {
        'ddlAddressSearchType': 'Starts with',
        'ddlCitySearchType': 'Starts with',
        'ddlCommitteeType': 'Select a Type',
        'ddlNameSearchType': 'Contains',
        'ddlOrderBy': 'Committee Name - A to Z',
        'ddlState': 'IL',
        'chkActive': 'True',
        'txtCity': 'Chicago'
    }
    scraper = CommitteeScraper(base_url, params)
    for committee in scraper.scrape_committees():
        # Save to DB and maybe write as JSON?
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
