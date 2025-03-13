# CyberThreatFlow

## Gathering reports, articles
The CyberThreatCrawler detects reports, articles from a given url, also crawl the websites seaching for more reports. If pagination is avaible in the correct format, then it uses it to gather all the avaible reports (currently only till the 7th page to save tokens).  
It also saves the found articles in a database.

## Is a report worth processing
IsReportWorthProcessing crew decide if a report is worth further processing in a cyber security view.

## Processing
ReportProcessing crew process analyze the report, and gather current and future threaths, saves them in a database.  
It also generates a short report on it.