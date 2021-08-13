import re
import os
import json
import requests
import datetime
import dateparser
# import streamlit as st

from lxml import html
from loguru import logger
from urllib.parse import urljoin
from pygooglenews import GoogleNews
from requests_html import HTMLSession

# internal imports begin here
from utilities import ScraperUtilities
from db_manager import NewsItem, DBManager


class GoogleScraper():
    BASEURL = 'https://www.google.com/search'
    search_slug = 'search?q={search_term}'

    def __init__(self):
        self.utils = ScraperUtilities
        self.config = self.utils.get_config()
        self.session = HTMLSession()
        self.search_terms = self.config['search_terms']
        self.db_manager = DBManager()

    # def get_config(self):
    #     file_dir = os.path.dirname(os.path.realpath('__file__'))
    #     file_path = os.path.join(file_dir, 'config.json')
    #     with open(file_path, 'r') as f:
    #         self.config = json.loads(f.read())
    #     assert self.config

    def get(self, url=None, slug=None, params=None):
        if slug:
            assert url is None
            url = urljoin(self.BASEURL, slug)
        return self.session.get(url, params=params)

    def get_search_news_slug(self, resp):
        news_elems = resp.html.xpath("//a[text()[contains(., 'News')]]")
        assert len(news_elems) == 1
        news_elem = news_elems[0]
        links = news_elem.links
        assert len(links) == 1
        return links.pop()

    def get_single_elem(self, parent, xpath):
        _elems = parent.xpath(xpath)
        assert len(_elems) == 1
        return _elems[0]

    def iter_search_news_data(self, resp):
        '''Return articles from the Google Search News tab.
        
        Inputs:
            - resp: response for request to Google Search News
        '''
        news_elems = resp.html.xpath("//g-card")
        for news_elem in news_elems:
            title = self.get_single_elem(news_elem, ".//div[@aria-level=2]").text
            description = self.get_single_elem(news_elem, ".//div[@class='Y3v8qd']").text
            description = description.split('.')[0]
            url = self.get_single_elem(news_elem, ".//a/@href")
            date = None  # Google search results do not provide date
            yield (url, title, description, date)

    def scrape_search_data(self):
        '''Scrape news data from Google Search.

        Function deprecated but retained for future use.
        '''
        session = self.db_manager.get_session()
        for search_term in self.search_terms:
            # st.write(f"# Keyword: {search_term}")
            params = {
                'q': search_term,
                'hl': 'en'
            }
            resp = self.get(self.BASEURL, params=params)
            news_slug = self.get_search_news_slug(resp)
            resp = self.get(slug=news_slug)
            for url, title, description, date in self.iter_search_news_data(resp):
                news_item = NewsItem(
                    url=url, title=title,
                    description=description,
                    date=date
                )
                existing_news_item = self.utils.get_if_exists(session, news_item, 'url')
                if existing_news_item:
                    logger.warning(f'News item already in database: {vars(news_item)}')
                else:
                    session.add(news_item)
                    logger.info(f'Added item: {vars(news_item)}')
            session.commit()
        session.close()


    def read_text_from_fragment(self, fragment):
        '''Read text from HTML fragment.'''
        tree = html.fromstring(fragment)
        _xpath = './a/text()'
        _text = self.get_single_elem(tree, _xpath)
        return _text

    def validate_news_item(self, news_item):
        assert news_item.url
        assert news_item.title
        assert news_item.description
        assert news_item.publishing_time

    def scrape_news_from_rss(self):
        '''Scrape articles from RSS feed.'''

        gn = GoogleNews(country='KE')

        session = self.db_manager.get_session()
        for search_term in self.search_terms:
            results = gn.search(search_term)
            entries = results.get('entries')
            assert entries

            for entry in entries:
                title = entry.get('title')
                url = entry['link']
                description_fragment = entry['summary']
                description = self.read_text_from_fragment(description_fragment)
                raw_date = entry['published']
                publishing_time = dateparser.parse(raw_date)

                news_item = NewsItem(
                title=title,
                url=url,
                description=description,
                publishing_time=publishing_time
                )

                self.validate_news_item(news_item)

                # do not insert news_items over 6 months old
                cutoff_date = datetime.datetime.now() - datetime.timedelta(weeks= (4*6))
                naive_publishing_time = news_item.publishing_time.replace(tzinfo=None)
                if naive_publishing_time < cutoff_date:
                    logger.warning('Skipping item because it is older than cutoff date')
                    continue

                existing_news_item = self.utils.get_if_exists(session, news_item, 'url')
                if existing_news_item:
                    logger.warning(f'News item already in database: {vars(news_item)}')
                else:
                    session.add(news_item)
                    logger.info(f'Added item to session: {vars(news_item)}')
            session.commit()
        session.close()


if __name__ == "__main__":
    crawler = GoogleScraper()
    crawler.scrape_news_from_rss()
