import asyncio
import logging
from typing import Optional
import pyppeteer
from pyppeteer.browser import Browser
from scrapy.settings import Settings
from twisted.internet.defer import Deferred
from .browser_request import BrowserRequest
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.utils.reactor import verify_installed_reactor



logger = logging.getLogger(__name__)


class ScrapyPyppeteerDownloaderMiddleware:
    """Downloader middleware handling the requests with Puppeteer

    Handles launching browser tabs, acts as a downloader.
    Probably eventually this should be moved to scrapy core as a downloader.
    """
    def __init__(self, settings: Settings):
        verify_installed_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
        self._browser: Optional[Browser] = None
        self._launch_options = settings.getdict('PYPPETEER_LAUNCH_OPTIONS') or {}
        self._navigation_timeout: Optional[int] = settings.getint("PYPPETEER_NAVIGATION_TIMEOUT") or None

    @classmethod
    async def _from_crawler(cls, crawler):
        middleware = cls(crawler.settings)
        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)
        return middleware

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware"""
        loop = asyncio.get_event_loop()
        middleware = loop.run_until_complete(
            asyncio.ensure_future(cls._from_crawler(crawler))
        )
        return middleware

    def process_request(self, request, spider):
        """Check if the Request should be handled by Puppeteer"""
        # if request.meta["pyppeteer"]:
        if isinstance(request, BrowserRequest):
            return _aio_as_deferred(self._process_request(request, spider))
        else:
            return None

    async def _process_request(self, request: BrowserRequest, spider):
        """Handle the request using Puppeteer"""
        if self._browser is None:
            self._browser = await pyppeteer.launch(**self._launch_options)

        page = await self._browser.newPage()
        if self._navigation_timeout is not None:
            page.setDefaultNavigationTimeout(self._navigation_timeout)

        n_tabs = _n_browser_tabs(self._browser)
        logger.debug(f'{n_tabs} tabs opened')

        # Cookies
        if isinstance(request.cookies, dict):
            await page.setCookie(*[
                {'name': k, 'value': v}
                for k, v in request.cookies.items()
            ])
        else:
            await page.setCookie(request.cookies)

        # # The headers must be set using request interception
        # await page.setRequestInterception(True)
        #
        # @page.on('request')   # not available
        # async def _handle_headers(pu_request):
        #     overrides = {
        #         'headers': {
        #             k.decode(): ','.join(map(lambda v: v.decode(), v))
        #             for k, v in request.headers.items()
        #         }
        #     }
        #     await pu_request.continue_(overrides=overrides)

        # await page.setRequestInterception(True)
        # page.on("request", modify_url)

        response = await page.goto(
            request.url,
            {
                'waitUntil': request.wait_until
            },
        )

        if request.wait_for:
            await page.waitFor(request.wait_for)

        # TODO
        # if request.screenshot:
        #     request.meta['screenshot'] = await page.screenshot()

        content = await page.content()
        body = str.encode(content)
        # make it available for callback function
        request.cb_kwargs['page'] = page

        # Necessary to bypass the compression middleware (?)
        response.headers.pop('content-encoding', None)
        response.headers.pop('Content-Encoding', None)

        return HtmlResponse(
            page.url,
            status=response.status,
            headers=response.headers,
            body=body,
            encoding='utf-8',
            request=request
        )

    async def _spider_closed(self):
        # should close only the page
        await self._browser.close()

    def spider_closed(self):
        """Shutdown the browser when spider is closed"""
        return _aio_as_deferred(self._spider_closed())


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
    """Transform a Twisted Deffered to an Asyncio Future"""
    return Deferred.fromFuture(asyncio.ensure_future(f))
