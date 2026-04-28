BOT_NAME = "salesforce_docs_spider"

SPIDER_MODULES = ["salesforce_docs_spider.spiders"]
NEWSPIDER_MODULE = "salesforce_docs_spider.spiders"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 0.25
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
TELNETCONSOLE_ENABLED = False
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
USER_AGENT = "salesforce-docs-rag/0.1 (+https://github.com/portfolio/salesforce-docs-rag)"
