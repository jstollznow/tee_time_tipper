import re
from typing import Any, Dict, List, Optional, Pattern, cast
import bs4
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from bs4.element import SoupStrainer
from requests.sessions import Session

class TipperScraper:
    TEE_TIME_OBJECT: Optional[Pattern[str]] = None
    TIME_OBJECT: Optional[Pattern[str]] = None
    AVAILABLE_SLOT: Optional[Pattern[str]] = None

    _request_session: Optional[Session] = None
    _strainer_filter: Optional[SoupStrainer] = None

    @staticmethod
    def set_scraping_details(xml_config: Dict[str, str]) -> None:
        TipperScraper.TEE_TIME_OBJECT = re.compile(xml_config['TEE_TIME_OBJECT'])
        TipperScraper.TIME_OBJECT = re.compile(xml_config['TIME_OBJECT'])
        TipperScraper.AVAILABLE_SLOT = re.compile(xml_config['AVAILABLE_SLOT'])

        TipperScraper._request_session = requests.session()
        TipperScraper._strainer_filter = SoupStrainer('div', re.compile(xml_config['TEE_TIMES_LIST']))

    @staticmethod
    def get_tee_times_for_date(bookings_url: str, tee_time_cut_off: datetime, min_spots: int, booking_ids: Dict[str, datetime]) -> List[Dict[str, Any]]:
        tee_times: List[Dict[str, Any]] = []
        soup: BeautifulSoup = BeautifulSoup(TipperScraper._get_content(bookings_url), 'lxml', parse_only=TipperScraper._strainer_filter)

        row: bs4.element.Tag
        for row in soup.find_all('div', TipperScraper.TEE_TIME_OBJECT):
            tee_time: datetime = datetime.combine(tee_time_cut_off.date(), TipperScraper._get_tee_time(row).time())
            group_id: str = row.get('id')[4:]
            booking_ids[group_id] = tee_time
            if tee_time.time() <= tee_time_cut_off.time():
                slots: List[str] = TipperScraper._get_spots_available(row)
                if len(slots) >= min_spots:
                    tee_times.append({
                        'group_id': group_id,
                        'slots': slots,
                        'tee_time': tee_time
                    })
            else:
                break

        return tee_times

    @staticmethod
    def _get_content(url: str) -> str:
        return cast(Session, TipperScraper._request_session).get(url).text

    @staticmethod
    def _get_tee_time(row: bs4.element.Tag):
        return datetime.strptime(row.find(TipperScraper.TIME_OBJECT).text.strip(), '%I:%M %p')

    @staticmethod
    def _get_spots_available(row: bs4.element.Tag) -> List[str]:
        slots: List[str] = []

        slot: bs4.element.Tag
        for slot in row.find_all("div", TipperScraper.AVAILABLE_SLOT):
            slots.append(slot.get('id'))

        return slots