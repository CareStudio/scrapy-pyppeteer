from scrapy.http.response import Response
from pyppeteer.page import Page


class BrowserResponse(Response):
    def __init__(self, *args, **kwargs):
        self.page: Page = kwargs.pop('page')
        super(BrowserResponse, self).__init__(*args, **kwargs)
