# scrapy-pyppeeteer: use pyppeteer from a Scrapy spider

- Forked from https://github.com/lopuhin/scrapy-pyppeteer

Current status is experimental, most likely the library will remain in experimental state, with a proper solution included in Scrapy later (which will be very different). Documentation assumes Scrapy knowledge.

## Installation
Python 3.6+ is required for `(PEP 525)[https://www.python.org/dev/peps/pep-0525/]` Asynchronous Generators .

Install scrapy-pyppeteer by:
```python
    pip install git+https://github.com/CareStudio/scrapy-pyppeteer.git
```

## Usage
At the moment, browser management is implemented as a downloader middleware, which you need to activate (update `DOWNLOADER_MIDDLEWARES` in settings)::
```python
   DOWNLOADER_MIDDLEWARES = {
       'scrapy_pyppeteer.ScrapyPyppeteerDownloaderMiddleware': 1000,
   }
```

In settings.py, install asyncio reactor by:
```python
# from scrapy.utils.reactor import install_reactor, verify_installed_reactor
# install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
```

After that you can use `scrapy_pyppeteer.BrowserRequest`, and you'll get `pyppeteer.page.Page` in your `parse` method. 

To do anything with `page`, you need to define your parse callback as `async def`, and use `await` syntax. All actions performed via `await` are executed directly, without going
to the scheduler (although in the same global event loop). You can also `yield` items and new requests, which will work normally.

Short example of the parse method
(see more self-contained examples in "examples" folder of this repo)
```python
    async def parse(self, response, page: pyppeteer.page.Page):
        yield {'url': response.url}
        for link in await page.querySelectorAll('a'):
            url = await page.evaluate('link => link.href', link)
            yield BrowserRequest(url)
        await page.close()
```

## Settings
- `PYPPETEER_LAUNCH_OPTIONS`: a dict with pyppeteer launch options, see `pyppeteer.launch` docstring.
- `PYPPETEER_NAVIGATION_TIMEOUT`: PYPPETEER_NAVIGATION_TIMEOUT

## TODO
- Set response status and headers
- A more ergonomic way to close the tab by default?
- More tests
- A way to schedule interactions reusing the same window
  (to continue working in the same time but go through the scheduler), making
  sure one tab is used only by one parse method.
- Nice extraction API (like parsel)
- A way to limit max number of tabs open (a bit tricky)


## Acknowledgements

This project was inspired by and modified based on:

* https://github.com/lopuhin/scrapy-pyppeteer
* https://github.com/clemfromspace/scrapy-puppeteer
* https://github.com/scrapy/scrapy/pull/1455
* https://github.com/michalmo/scrapy-browser