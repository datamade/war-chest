import scrapelib
import json
import lxml.html
import xmltodict
import traceback
from collections import defaultdict
import datetime

class DotNetScraper(scrapelib.Scraper) :
    def __init__(self,
                 raise_errors=True,
                 requests_per_minute=60,
                 follow_robots=True,
                 retry_attempts=0,
                 retry_wait_seconds=5,
                 header_func=None,
                 data_row_xpath=None,
                 base_url=None,
                 date_format='%m/%d/%Y'):

        self.base_url = base_url
        self.date_format=date_format
        self.data_row_xpath=data_row_xpath
        super(DotNetScraper, self).__init__(raise_errors,
                                            requests_per_minute,
                                            follow_robots,
                                            retry_attempts,
                                            retry_wait_seconds,
                                            header_func)

    def lxmlize(self, url, payload=None):
        entry = self.urlopen(url, 'POST', payload)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def sessionSecrets(self, page) :

        payload = {}
        #print page.xpath("//input[@name='__EVENTARGUMENT']/@value")
        payload['__EVENTARGUMENT'] = None
        payload['__VIEWSTATE'] = page.xpath("//input[@name='__VIEWSTATE']/@value")[0]
        payload['__EVENTVALIDATION'] = page.xpath("//input[@name='__EVENTVALIDATION']/@value")[0]

        return(payload)

    def parseDataTable(self, table):
        """
        Legistar uses the same kind of data table in a number of
        places. This will return a list of dictionaries using the
        table headers as keys.
        """
        headers = table.xpath('.//th')
        rows = table.xpath(self.data_row_xpath)


        keys = {}
        for index, header in enumerate(headers):
            keys[index] = '\n'.join(header.xpath('.//text()')).replace('&nbsp;', ' ').strip()

        for row in rows:
          try:
            data = defaultdict(lambda : None)

            for index, field in enumerate(row.xpath("./td")):
                key = keys[index]
                value = '\n'.join(field.xpath('.//text()')).replace('&nbsp;', ' ').strip()

                try:
                    value = datetime.datetime.strptime(value, self.date_format)
                except ValueError:
                    pass

                # Is it a link?
                address = None
                link = field.xpath('.//a')
                if len(link) > 0 :
                    address = self._get_link_address(link[0])
                if address is not None:
                    value = {'label': value, 'url': address}

                data[key] = value

            yield data, keys, row

          except Exception as e:
            print 'Problem parsing row:'
            print row
            print traceback.format_exc()
            raise e

    def _get_link_address(self, link):
        # If the link doesn't start with a #, then it'll send the browser
        # somewhere, and we should use the href value directly.
        href = link.get('href')
        if href is not None and href != self.base_url :
          return href

        # If it does start with a hash, then it causes some sort of action
        # and we should check the onclick handler.
        else:
          onclick = link.get('onclick')
          if onclick is not None and 'open(' in onclick :
            return self.base_url + onclick.split("'")[1]

        # Otherwise, we don't know how to find the address.
        return None


class CandidateScraper(DotNetScraper) :
    def __init__(self,
                 raise_errors=True,
                 requests_per_minute=60,
                 follow_robots=True,
                 retry_attempts=0,
                 retry_wait_seconds=5,
                 header_func=None) :
        base_url='http://www.elections.il.gov/campaigndisclosure/'
        data_row_xpath=".//tr[starts-with(@class, 'SearchListTableRow')]"
        super(CandidateScraper, self).__init__(raise_errors,
                                               requests_per_minute,
                                               follow_robots,
                                               retry_attempts,
                                               retry_wait_seconds,
                                               header_func,
                                               data_row_xpath,
                                               base_url)


    def candidate_box(self, page) :
        table = page.xpath("//table[@class='SearchPanel']")[0]
        spans = table.xpath(".//span[starts-with(@id, 'ctl00_ContentPlaceHolder1_')]")

        d = defaultdict(lambda : None)
        for span in spans :
            k = span.get('id').split('ctl00_ContentPlaceHolder1_lbl')[1]
            v = '\n'.join(span.xpath('.//text()')).replace('&nbsp;', ' ').strip()
            d[k] = v
        
        return d


s = CandidateScraper(requests_per_minute=60,
                     follow_robots=True,
                     raise_errors=True,
                     retry_attempts=10)

s.cache_storage = scrapelib.cache.FileCache('cache')
s.cache_write_only = False



def candidate_pages() :
    candidates_page_url = 'http://www.elections.il.gov/CampaignDisclosure/CandidateDetail.aspx?ID=%s'

    blank_pages = 0
    election_id = 1
    last_candidate = False
    while not last_candidate :
        url = candidates_page_url % election_id
        response = s.lxmlize(url)

        if 'SearchListTableRow' in lxml.html.tostring(response) :
            blank_pages = 0
            yield election_id, url, response 
        else :
            blank_pages += 1
            if blank_pages > 10 :
                last_candidate = True

        election_id += 1


candidates = []
for election_id, url, page in candidate_pages() :
    print election_id
    candidate = {}
    candidate['url'] = url
    candidate['Candidate ID'] = election_id
    candidate.update(s.candidate_box(page))


    candidate['results'] = []
    candidate_results_table = page.xpath("//table[@id='ctl00_ContentPlaceHolder1_tblCandidateResults']")[0]
    for result, _, _ in s.parseDataTable(candidate_results_table) :
        candidate['results'].append(dict(result))

    candidate['committees'] = []
    committee_table = page.xpath("//table[@id='ctl00_ContentPlaceHolder1_tblCommitteeInformation']")[0]
    for committee, _, _ in s.parseDataTable(committee_table) :
        committee['url'] = committee['Committee Name']['url']
        committee['Committee Name'] = committee['Committee Name']['label']
        committee_ids = committee['ID'].split('\n')
        for committee_id in committee_ids :
            if 'State' in committee_id :
                committee['State ID'] = committee_id.split()[-1]
            elif 'Local' in committee_id :
                committee['Local ID'] = committee_id.split()[-1]
            elif 'Committee ID' in committee_id :
                committee['Committee ID'] = committee_id.split()[-1]
        del committee['ID']
        candidate['committees'].append(dict(committee))
    candidates.append(candidate)


with open('candidates.json', 'w') as outfile :
  json.dump(candidates, 
            outfile, 
            sort_keys=True, 
            indent=4, 
            separators=(',', ': '))
           

