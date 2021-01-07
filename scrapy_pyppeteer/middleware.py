import asyncio
import logging
from typing import Optional

import pyppeteer
from pyppeteer.browser import Browser
from scrapy.settings import Settings
from twisted.internet.defer import Deferred

from .browser_request import BrowserRequest
from .browser_response import BrowserResponse

from scrapy.utils.reactor import verify_installed_reactor
from scrapy.crawler import Crawler
from scrapy.http import Request, Response
from scrapy.http.headers import Headers
from scrapy.responsetypes import responsetypes
from scrapy.statscollectors import StatsCollector
from scrapy.utils.defer import deferred_from_coro


logger = logging.getLogger(__name__)


class ScrapyPyppeteerDownloaderMiddleware:
    """ Handles launching browser tabs, acts as a downloader.
    Probably eventually this should be moved to scrapy core as a downloader.
    """
    def __init__(self, settings: Settings):
        verify_installed_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
        self._browser: Optional[Browser] = None
        self._launch_options = settings.getdict('PYPPETEER_LAUNCH_OPTIONS') or {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        if isinstance(request, BrowserRequest):
            return _aio_as_deferred(self.process_browser_request(request))
        else:
            return request

    async def process_browser_request(self, request: BrowserRequest):
        if self._browser is None:
            self._browser = await pyppeteer.launch(**self._launch_options)
        page = await self._browser.newPage()
        n_tabs = _n_browser_tabs(self._browser)
        logger.debug(f'{n_tabs} tabs opened')
        if request.is_blank:
            url = request.url
        else:
            response = await page.goto(request.url)
            url = page.url
            # TODO set status and headers
        return BrowserResponse( url=url,  page=page, )

        # TODO: how to enable Response have the selector?
        # body = (await page.content()).encode("utf8")
        # print(f"SOONG body{body}")
        # headers = Headers(response.headers)
        # return BrowserResponse( url=url,  page=page, 
        #     status=response.status,
        #     headers=headers,   # will cause httpresponse
        #     body=body,
        #     request=request
        #     )


def _n_browser_tabs(browser: Browser) -> int:
    """ A quick way to get the number of browser tabs.
    """
    n_tabs = 0
    for context in browser.browserContexts:
        for target in context.targets():
            if target.type == 'page':
                n_tabs += 1
    return n_tabs


def _aio_as_deferred(f):
    return Deferred.fromFuture(asyncio.ensure_future(f))
