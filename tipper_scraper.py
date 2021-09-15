import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from bs4.element import SoupStrainer

from tee_time_group import TeeTimeGroup

class TipperScraper:
    TEE_TIMES_LIST = ''
    TEE_TIME_OBJECT = ''
    TIME_OBJECT = ''
    AVAILABLE_SLOT = ''

    TIMETABLE_ENDPOINT = ''
    ADD_TO_CART_ENDPOINT = ''
    CHECKOUT_ENDPOINT = ''

    __request_session = None
    __strainer_filter = None

    @staticmethod
    def set_scraping_details(xml_config):
        TipperScraper.TEE_TIMES_LIST = re.compile(xml_config['TEE_TIMES_LIST'])
        TipperScraper.TEE_TIME_OBJECT = re.compile(xml_config['TEE_TIME_OBJECT'])
        TipperScraper.TIME_OBJECT = re.compile(xml_config['TIME_OBJECT'])
        TipperScraper.AVAILABLE_SLOT = re.compile(xml_config['AVAILABLE_SLOT'])
        TipperScraper.__request_session = requests.session()
        TipperScraper.__strainer_filter = SoupStrainer('div', TipperScraper.TEE_TIMES_LIST)

    @staticmethod
    def get_tee_times_for_date(bookings_url, tee_time_cut_off, min_spots, booking_ids):
        tee_times = set()
        soup = BeautifulSoup(TipperScraper.__get_content(bookings_url), 'lxml', parse_only=TipperScraper.__strainer_filter)
        for row in soup.find_all('div', TipperScraper.TEE_TIME_OBJECT):
            tee_time = datetime.combine(tee_time_cut_off.date(), TipperScraper.__get_tee_time(row).time())
            group_id = row.get('id')[4:]
            booking_ids[group_id] = tee_time
            if tee_time.time() <= tee_time_cut_off.time():
                slots = TipperScraper.__get_spots_available(row)
                if len(slots) >= min_spots:
                    tee_times.add(TeeTimeGroup(group_id, slots, tee_time))
            else:
                break
        return tee_times

    @staticmethod
    def __get_content(url):
        return TipperScraper.__request_session.get(url).text

    @staticmethod
    def __get_tee_time(row):
        time = datetime.strptime(row.find(TipperScraper.TIME_OBJECT).text.strip(), '%I:%M %p')
        return time

    @staticmethod
    def __get_spots_available(row):
        slots = []
        for slot in row.find_all("div", TipperScraper.AVAILABLE_SLOT):
            slots.append(slot.get('id'))
        return slots