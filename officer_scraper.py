import scrapelib
import lxml.html

class OfficerScraper(scrapelib.Scraper):
    def __init__(self,
                 raise_errors=False,
                 requests_per_minute=60,
                 follow_robots=True,
                 retry_attempts=0,
                 retry_wait_seconds=5,
                 header_func=None):
        super(OfficerScraper, self).__init__(raise_errors,
                                               requests_per_minute,
                                               follow_robots,
                                               retry_attempts,
                                               retry_wait_seconds,
                                               header_func,)

    def scrape_officers(self, url):
        page = self.lxmlize(url)
        officer_link = page.xpath('//a[@id="ctl00_ContentPlaceHolder1_hypLinkToOfficers"]')


    def lxmlize(self, url, payload=None):
        if payload :
            entry = self.urlopen(url, 'POST', payload)
        else :
            entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

if __name__ == "__main__":
    from app import db, Committee, Officer
    scraper = OfficerScraper(retry_attempts=5)
    scraper.cache_storage = scrapelib.cache.FileCache('cache')
    scraper.cache_write_only = False
    comms = db.session.query(Committee).all()
    for comm in comms:
        officers = scraper.scrape_officers(comm.url)
       # for officer in officers:
       #     o = Officer(**officer)
       #     setattr(o, 'committee', comm)
       #     db.session.add(o)
       #     db.session.commit()


