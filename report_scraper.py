import scrapelib
from app import db, Candidate, Committee, Report, Officer
from datetime import date, datetime
from urlparse import parse_qs, urlparse
from sqlalchemy.sql import or_
from operator import itemgetter
from itertools import groupby
import lxml.html

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
        if payload :
            entry = self.urlopen(url, 'POST', payload)
        else :
            entry = self.urlopen(url)
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

class ReportScraper(DotNetScraper):
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
        super(ReportScraper, self).__init__(raise_errors,
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
                reports = page.xpath("//tr[starts-with(@class, '%s')]" % self.report_row)
                for report in reports:
                    report_data = {}
                    raw_period = report.find("td[@headers='%s']/span" % self.report_period_cell).xpath('.//text()')
                    if raw_period:
                        report_data['period_from'], report_data['period_to'] = self._parse_period(raw_period)
                    date_filed = report.find("td[@headers='ctl00_ContentPlaceHolder1_thFiled']/span").text
                    date, time, am_pm = date_filed.split(' ')
                    date = '/'.join([d.zfill(2) for d in date.split('/')])
                    time = ':'.join([t.zfill(2) for t in time.split(':')])
                    report_data['date_filed'] = datetime.strptime(' '.join([date, time, am_pm]), '%m/%d/%Y %I:%M:%S %p')
                    detailed = report.find("td[@headers='%s']/a" % self.report_type_cell)
                    if detailed is not None:
                        report_data['type'] = detailed.text
                        detail_url = detailed.attrib['href']
                        report_data['detail_url'] = detail_url
                        qs = parse_qs(urlparse(detail_url).query)
                        try:
                            report_id = qs['id']
                        except KeyError:
                            report_id = qs['FiledDocID']
                        report_data['id'] = report_id[0]
                        report_detail = self.lxmlize(detail_url)
                        funds_start = report_detail.xpath("//span[@id='%s']" % self.detail_funds_start)
                        # TODO: Looks like there are Pre-Election reports are formatted differently
                        # Need to be able to get funding data from all report formats
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
                        invest_total = report_detail.xpath("//span[@id='ctl00_ContentPlaceHolder1_lblTotalInvest']")
                        if receipts:
                            report_data['invest_total'] = self._clean_float(invest_total[0].text)
                    # For now skipping reports with no details page
                    #else:
                    #    detailed = report.find("td[@headers='%s']/span" % self.report_type_cell)
                    #    raw_period = report.find("td[@headers='%s']/span" % self.report_period_cell).text
                    #    if raw_period:
                    #        report_data['period_from'], report_data['period_to'] = self._parse_period(raw_period)
                    #    report_data['type'] = detailed.text
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
        if len(raw_period) > 1:
            raw_period = raw_period[1]
        else:
            raw_period = raw_period[0]
        period = raw_period.split(' to ')
        period_to = None
        period_from = None
        if len(period) > 1:
            f_month, f_day, f_year = period[0].strip().split('/')
            t_month, t_day, t_year = period[1].strip().split('/')
            period_from = date(int(f_year), int(f_month), int(f_day))
            period_to = date(int(t_year), int(t_month), int(t_day))
        else:
            year = raw_period.strip().split(' ')[0]
            try:
                period_from = date(int(year), 1, 1)
            except ValueError:
                pass
        return period_from, period_to

if __name__ == "__main__":
    scraper = ReportScraper(retry_attempts=5)
    scraper.cache_storage = scrapelib.cache.FileCache('cache')
    scraper.cache_write_only = False
    res = db.session.query(Candidate, Officer)\
        .filter(Officer.title.like('Chair%'))\
        .filter(Officer.candidate_id == Candidate.id).all()
    s = sorted(res, key=itemgetter(0))
    cands = {}
    for k,g in groupby(s, key=itemgetter(0)):
        cands[k] = []
        for off in list(g):
            cands[k].append(off[1].committee)
    for c in Candidate.query.filter(Candidate.current_office_holder == True).all():
        if cands.get(c):
            cands[c].extend([d for d in c.committees if d not in cands[c]])
        else:
            cands[c] = c.committees
    for cand, comms in cands.items():
        for committee in comms:
            for report_data in scraper.scrape_reports(committee.url):
                report_data['committee'] = committee
                if report_data.get('id'):
                    report = Report.query.get(int(report_data['id']))
                if report:
                    for k,v in report_data.items():
                        setattr(report, k, v)
                    db.session.add(report)
                    db.session.commit()
                else:
                    report = Report(**report_data)
                    db.session.add(report)
                    db.session.commit()
