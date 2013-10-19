import scrapelib
from candidates_scraper import DotNetScraper
from app import db, Candidate, Committee, Report
from datetime import date
from urlparse import parse_qs, urlparse

class CommitteeScraper(DotNetScraper):
    def __init__(self,
                 raise_errors=False,
                 requests_per_minute=60,
                 follow_robots=True,
                 retry_attempts=0,
                 retry_wait_seconds=5,
                 header_func=None):
        self.report_row = 'SearchListTableRow'
        self.report_type_cell = 'ctl00_ContentPlaceHolder1_thReportType'
        self.report_period_cell = 'ctl00_ContentPlaceHolder1_thReportingPeriod'
        self.page_counter = 'ctl00_ContentPlaceHolder1_lbRecordsInfo'
        self.detail_funds_start = 'ctl00_ContentPlaceHolder1_lblBegFundsAvail'
        self.detail_funds_end = 'ctl00_ContentPlaceHolder1_lblEndFundsAvail'
        self.detail_receipts = 'ctl00_ContentPlaceHolder1_lblTotalReceiptsTot'
        self.detail_expend = 'ctl00_ContentPlaceHolder1_lblTotalExpendTot'
        self.url_pattern = 'http://www.elections.il.gov/CampaignDisclosure/CommitteeDetail.aspx?id=%s&pageindex=%s'
        super(CommitteeScraper, self).__init__(raise_errors,
                                               requests_per_minute,
                                               follow_robots,
                                               retry_attempts,
                                               retry_wait_seconds,
                                               header_func,)
    
    def scrape_reports(self, url):
        start_page = self.lxmlize(url)
        committee_id = parse_qs(urlparse(url).query)['id'][0]
        print url
        for page in self._grok_pages(start_page, committee_id):
            if page is not None:
                reports = page.xpath("//tr[@class='%s']" % self.report_row)
                for report in reports:
                    report_data = {}
                    raw_period = report.find("td[@headers='%s']/span" % self.report_period_cell).text
                    if raw_period:
                        report_data['period_from'], report_data['period_to'] = self._parse_period(raw_period)
                    detailed = report.find("td[@headers='%s']/a" % self.report_type_cell)
                    if detailed is not None:
                        report_data['type'] = detailed.text
                        detail_url = detailed.attrib['href']
                        report_data['detail_url'] = detail_url
                        print detail_url
                        report_id = parse_qs(urlparse(detail_url).query).get('id')
                        if report_id:
                            report_detail = self.lxmlize(detail_url)
                            funds_start = report_detail.xpath("//span[@id='%s']" % self.detail_funds_start)
                            if funds_start:
                                report_data['funds_start'] = self._clean_float(funds_start[0].text)
                            funds_end = report_detail.xpath("//span[@id='%s']" % self.detail_funds_end)
                            if funds_end:
                                report_data['funds_end'] = self._clean_float(funds_end[0].text)
                            expenditures = report_detail.xpath("//span[@id='%s']" % self.detail_expend)
                            if expenditures:
                                report_data['expenditures'] = self._clean_float(expenditures[0].text)
                            receipts = report_detail.xpath("//span[@id='%s']" % self.detail_receipts)
                            if receipts:
                                report_data['receipts'] = self._clean_float(receipts[0].text)
                    else:
                        detailed = report.find("td[@headers='%s']/span" % self.report_type_cell)
                        raw_period = report.find("td[@headers='%s']/span" % self.report_period_cell).text
                        if raw_period:
                            report_data['period_from'], report_data['period_to'] = self._parse_period(raw_period)
                        report_data['type'] = detailed.text
                    yield report_data

    def _grok_pages(self, start_page, committee_id):
        page_counter = start_page.xpath("//span[@id='%s']" % self.page_counter)[0].text
        if page_counter:
            page_count = (int(page_counter.split(' ')[-1]) / 15) + 1
            if page_count > 1:
                for page_num in range(page_count):
                    url = self.url_pattern % (committee_id, page_num)
                    yield self.lxmlize(url)
            else:
                yield start_page
        else:
            yield None

    def _clean_float(self, num):
       num = num.replace(',', '').replace('$', '') 
       if num.find('(') is 0:
           num = '-' + num.replace('(', '').replace(')', '')
       return float(num)

    def _parse_period(self, raw_period):
        period = raw_period.split(' to ')
        period_to = None
        period_from = None
        if len(period) > 1:
            f_month, f_day, f_year = period[0].split('/')
            t_month, t_day, t_year = period[1].split('/')
            period_from = date(int(f_year), int(f_month), int(f_day))
            period_to = date(int(t_year), int(t_month), int(t_day))
        else:
            year = raw_period.split(' ')[0]
            try:
                period_from = date(int(year), 1, 1)
            except ValueError:
                pass
        return period_from, period_to
        

if __name__ == "__main__":
    committees = []
    for cands in Candidate.query.all():
        committees.extend(cands.committees)
    scraper = CommitteeScraper()
    scraper.cache_storage = scrapelib.cache.FileCache('cache')
    scraper.cache_write_only = False
    for committee in committees:
        for report_data in scraper.scrape_reports(committee.url):
            report_data['committee'] = committee
            report = Report.query.filter_by(**report_data).first()
            if not report:
                report = Report(**report_data)
                db.session.add(report)
                db.session.commit()
