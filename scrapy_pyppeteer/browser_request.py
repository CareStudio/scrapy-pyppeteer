"""This module contains the ``PuppeteerRequest`` class"""

from scrapy import Request


class BrowserRequest(Request):
    def __init__(self, url, callback=None, wait_until=None, wait_for=None, *args, **kwargs):
        """Initialize a new Puppeteer request
        Parameters
        ----------
        wait_until: basestring
            One of "load", "domcontentloaded", "networkidle0", "networkidle2".
            See https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.goto
        """

        self.wait_until = wait_until or 'domcontentloaded'
        self.wait_for = wait_for
        # self.screenshot = screenshot

        super().__init__(url, callback, *args, **kwargs)