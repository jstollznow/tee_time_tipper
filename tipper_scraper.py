import re
import requests
import lxml
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from bs4.element import SoupStrainer

from tee_time_group import TeeTimeGroup

class TipperScraper:
    TEE_TIMES_LIST = ''
    TEE_TIME_OBJECT = ''
    TIME_OBJECT = ''
    AVAILABLE_SLOT = ''

    BOOKING_ENDPOINT = ''
    ADD_TO_CART_ENDPOINT = ''
    CHECKOUT_ENDPOINT = ''

    def __init__(self) -> None:
        self.request_session = requests.session()
        self.strainer_filter = SoupStrainer('div', TipperScraper.TEE_TIMES_LIST)

    @staticmethod
    def set_scraping_details(xml_config, endpoints_config):
        TipperScraper.TEE_TIMES_LIST = re.compile(xml_config['TEE_TIMES_LIST'])
        TipperScraper.TEE_TIME_OBJECT = re.compile(xml_config['TEE_TIME_OBJECT'])
        TipperScraper.TIME_OBJECT = re.compile(xml_config['TIME_OBJECT'])
        TipperScraper.AVAILABLE_SLOT = re.compile(xml_config['AVAILABLE_SLOT'])

        TipperScraper.BOOKING_ENDPOINT = endpoints_config['booking_timetable']
        TipperScraper.ADD_TO_CART_ENDPOINT = endpoints_config['add_tee_time_to_cart']
        TipperScraper.CHECKOUT_ENDPOINT = endpoints_config['checkout']

    def get_tee_times_for_date(self, bookings_url, tee_time_cut_off, min_spots, booking_ids):
        tee_times = set()
        soup = BeautifulSoup(self.__get_content(bookings_url), 'lxml', parse_only=self.strainer_filter)
        for row in soup.find_all('div', self.TEE_TIME_OBJECT):
            tee_time = datetime.combine(tee_time_cut_off.date(), self.__get_tee_time(row).time())
            group_id = row.get('id')[4:]
            booking_ids[group_id] = str(tee_time)
            if tee_time.time() <= tee_time_cut_off.time():
                slots = self.__get_spots_available(row)
                if len(slots) >= min_spots:
                    tee_times.add(TeeTimeGroup(group_id, slots, tee_time))
            else:
                break
        return tee_times

    def __get_content(self, url):
        return self.request_session.get(url).text

    def __get_tee_time(self, row):
        time = datetime.strptime(row.find(self.TIME_OBJECT).text.strip(), '%I:%M %p')
        return time

    def __get_spots_available(self, row):
        slots = []
        for slot in row.find_all("div", self.AVAILABLE_SLOT):
            slots.append(slot.get('id'))
        return slots