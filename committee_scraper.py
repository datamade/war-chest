import scrapelib
import requests
from candidates_scraper import DotNetScraper
from app import db, Committee
from urllib import urlencode
import lxml.html

class CommitteeScraper(DotNetScraper):
    def __init__(self, base_url, params,
        raise_errors=False,
        requests_per_minute=60,
        follow_robots=False,
        retry_attempts=0,
        retry_wait_seconds=5,
        header_func=None):
        super(CommitteeScraper, self).__init__(raise_errors,
                                               requests_per_minute,
                                               follow_robots,
                                               retry_attempts,
                                               retry_wait_seconds,
                                               header_func,)
        self.base_url = base_url
        self.params = params

    def scrape_committees(self):
        print [p for p in self._grok_pages()]

    def _grok_pages(self):
        query_string = urlencode(self.params)
        url = '%s?%s' % (self.base_url, query_string)
        start_page = self.urlopen(url)
        page = lxml.html.fromstring(start_page)
        #page.make_links_absolute(url)
        page_counter = page.xpath("//span[@id='ctl00_ContentPlaceHolder1_lbRecordsInfo']")[0].text
        if page_counter:
            page_count = (int(page_counter.split(' ')[-1]) / 10)
            if page_count > 0:
                for page_num in range(page_count):
                    self.params['pageindex'] = page_num
                    qs = urlencode(self.params)
                    url = '%s?%s' % (self.base_url, qs)
                    # yield self.lxmlize(url)
                    yield url
            else:
                yield query_string
        else:
            yield None

if __name__ == "__main__":
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
    scraper = CommitteeScraper(base_url, params, retry_attempts=5)
    scraper.cache_storage = scrapelib.cache.FileCache('cache')
    scraper.cache_write_only = False
    scraper.scrape_committees()
