import re
import json
import urllib
import requests
import dateparser

from lxml import html
from loguru import logger

from tables import DbManager
from tables import Country, Threat, Date, Value


class KasperskyScraper():
    """Scrape cybersecurity statistics from Kaspersky."""

    BASEURL = 'https://cybermap.kaspersky.com/'
    country_stats_slug = "/data/securelist/graph_{threat_id}_w_{country_id}.json"

    def __init__(self, countries):
        """Initialize scraper with countries required."""
        self.db_manager = DbManager()
        self.session = self.db_manager.get_session()
        self.countries = countries
        self.set_ids()
        self.fill_countries_and_threats()

    def make_get_request(self, slug):
        """Make get request to given slug."""
        _url = urllib.parse.urljoin(self.BASEURL, slug)
        logger.info('Navigating to {}', _url)
        response = requests.get(_url)
        logger.info('Navigated to {} with response code {}', _url, response.status_code)
        return response

    def get_country_ids(self, content):
        """Return dict of country names and IDs."""
        countries = self.countries
        country_ids = []
        json_re = re.findall('window.countriesAll = (\[.+\])', content)
        assert json_re
        json_str = json_re[0]
        _json = json.loads(json_str)
        for country_dict in _json:
            if country_dict['name'] in countries:
                _temp = {'name': country_dict['name'], 'id': country_dict['id']}
                country_ids.append(_temp)
        return country_ids

    def get_threat_ids(self, content):
        """Return dict of threat type and IDs."""
        threat_ids = []
        content = html.fromstring(content)
        threat_elems = content.xpath('//select[@id="world_stats_detection_type"]/option')

        for threat_elem in threat_elems:
            _temp = {}
            _temp['id'] = threat_elem.get('value')
            _temp['full_name'] = threat_elem.text
            threat_ids.append(_temp)
        return threat_ids

    def set_ids(self):
        """Set country_ids and threat_ids as class variables."""
        # stats_page
        response = self.make_get_request('/stats')
        response_str = response.content.decode('utf8')
        self.country_ids = self.get_country_ids(response_str)
        self.threat_ids = self.get_threat_ids(response_str)

    def fill_countries_and_threats(self):
        """Fill country and threat information in database."""
        for country_dict in self.country_ids:
            existing_country = self.session.query(Country).filter(
                Country.id == country_dict['id']
            ).one_or_none()

            if existing_country:
                country = existing_country
                logger.info(f'{country.__dict__} already in database.')
            else:
                country = Country()
                country.name = country_dict['name']
                country.id = country_dict['id']
                logger.info(f'{country.__dict__} added to database')
            self.session.add(country)
        self.session.commit()

        for threat_dict in self.threat_ids:
            existing_threat = self.session.query(Threat).filter(
                Threat.id == threat_dict['id']
            ).one_or_none()

            if existing_threat:
                threat = existing_threat
                logger.info(f'{threat.__dict__} already in database.')
            else:
                threat = Threat()
                threat.id = threat_dict['id']
                threat.name = threat_dict['full_name']
                logger.info(f'{threat.__dict__} added to database')
                self.session.add(threat)

        self.session.commit()

    def fill_values_in_database(self):
        """Fill values in database."""
        self.dates = set()
        values = []

        for country_dict in self.country_ids:
            country_id = country_dict['id']

            country = self.session.query(Country).filter(
                Country.id == country_id
            ).one()

            for threat_dict in self.threat_ids:
                threat_id = threat_dict['id']

                threat = self.session.query(Threat).filter(
                    Threat.id == threat_id
                ).one()

                slug = self.country_stats_slug.format(
                    country_id=country_id,
                    threat_id=threat_id.lower()
                )
                response = self.make_get_request(slug)
                response = response.json()
                for value_dict in response:
                    date = Date()
                    _date = dateparser.parse(value_dict['date']).date()
                    date.value = _date

                    existing_date = self.session.query(Date).filter(
                        Date.value == date.value
                    ).one_or_none()
                    if existing_date is None:
                        self.session.add(date)
                        self.session.commit()
                        logger.info(f'{date.value} added to database')
                        self.session.commit()
                    else:
                        date = existing_date

                    value = Value()
                    value.date = date
                    value.country = country
                    value.threat = threat
                    value.value = value_dict['count']
                    values.append(value)
                    self.session.add(value)
                    self.session.commit()

                    assert self.session.query(Value).filter(
                        Value.date == date,
                        Value.country == country,
                        Value.threat == threat,
                        Value.value == value_dict['count']
                    ).one()

                    self.dates.add(_date)

        # self.session.bulk_save_objects(values)
        self.session.commit()
        logger.info('Values filled in database')


if __name__ == "__main__":
    scraper = KasperskyScraper(['Kenya', 'Nigeria', 'South Africa'])
    scraper.fill_values_in_database()
    # scraper.fill_database()
