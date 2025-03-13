#!/usr/bin/env python
from random import randint

from pydantic import BaseModel

from crewai.flow import Flow, listen, start

from cyberthreat_article_process.crawler.cyber_threat_crawler import CyberThreatCrawler

from cyberthreat_article_process.crews.is_report_worth_processing.is_report_worth_processing import IsReportWorthProcessing
from cyberthreat_article_process.crews.report_processing.report_processing import ReportProcessing


class CyberThreatFlow(Flow):
    START_URL = "https://krebsonsecurity.com/"
    scraper = CyberThreatCrawler(start_url=START_URL)
    

    @start()
    def scrape_articles(self):
        print("Scrape given website")
        START_URL = "https://krebsonsecurity.com/"
        self.scraper.scrape_all_pages_dynamic(START_URL)
        
    @listen(scrape_articles)
    def process_articles(self):
        unprocessed = self.scraper.get_unprocessed_articles()
        for report in unprocessed[:2]:
            result = (IsReportWorthProcessing().crew().kickoff(inputs={"report" : report}))
            print(f"Report: {result} - {report['metadata']['title']} - {report['metadata']['url']}")
            print(str(result).strip().lower())
            if (str(result).strip().lower() == "approved"):
                ReportProcessing().crew().kickoff(inputs={"report" : report})
                self.scraper.mark_article_as_processed(report['id'])
    
    @listen(process_articles)
    def processed_articles(self):
        processed_articles = self.scraper.get_processed_articles()
        for article in processed_articles:
            print(f"📄 {article['metadata']['title']} - {article['metadata']['url']}")


def kickoff():
    poem_flow = CyberThreatFlow()
    poem_flow.kickoff()


def plot():
    poem_flow = CyberThreatFlow()
    poem_flow.plot()


if __name__ == "__main__":
    kickoff()
