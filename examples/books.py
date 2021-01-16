import scrapy
from scrapy_pyppeteer import BrowserRequest
from pyppeteer.page import Page



class BooksSpider(scrapy.Spider):
    """ Example spider for books.toscrape.com, using the headless browser
    for all scraping, based on https://github.com/scrapy/booksbot/.
    Run with::

        scrapy runspider examples/books.py

    """
    name = 'books'
    start_url = 'http://books.toscrape.com'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_pyppeteer.ScrapyPyppeteerDownloaderMiddleware': 1000,
        },
        'CONCURRENT_REQUESTS': 8,
    }

    def start_requests(self):
        yield BrowserRequest(self.start_url)

    async def parse(self, response, page: Page):
        yield {'url': response.url}
        for link in await page.querySelectorAll('a'):
            url = await page.evaluate('link => link.href', link)
            yield BrowserRequest(url)
        await page.close()





# the runer
from scrapy.crawler import CrawlerProcess
process = CrawlerProcess(settings={
    # "FEEDS": {
    #     "items.json": {"format": "json"},
    # },
})

process.crawl(BooksSpider)
process.start() # the script will block here until the crawling is finished