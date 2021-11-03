from datetime import date, datetime
import json
import os
import errno
from typing import Any, Dict, List

from program_args import get_args
from golf_round_type import GolfRoundType
from tee_time_group import TeeTimeGroup

class GolfCourse:
    BOOKING_ENDPOINT: str = ''
    ADD_TO_CART_ENDPOINT: str = ''
    CHECKOUT_ENDPOINT: str = ''

    def __init__(self, course_config: Any) -> None:
        self.name: str = course_config['name']
        self._id: str = course_config['course_id']
        self._cache_path: str = os.path.join(os.path.dirname(__file__), "cache", f"{self.name.lower().replace(' ', '_')}.json")
        self._booking_ids_path: str = os.path.join(os.path.dirname(__file__), "booking_ids", f"{self.name.lower().replace(' ', '_')}.json")
        self._base_url: str = course_config['url']
        self.checkout_url: str = self._base_url + self.CHECKOUT_ENDPOINT
        self._lookahead_days: int = course_config.get('lookahead_days', 14)
        self._round_types: Dict[str, GolfRoundType] = {}

        base_timetable_url: str = self._get_base_timetable_url()
        base_add_to_cart_url: str = self._base_url + self.ADD_TO_CART_ENDPOINT

        for fee_group_config in course_config['fee_groups']:
            round: GolfRoundType = GolfRoundType(fee_group_config, base_timetable_url, base_add_to_cart_url)
            self._round_types[round.id] = round

        self.deserialize(self._load_json_from_path(self._cache_path))
        self._set_booking_ids(self._load_json_from_path(self._booking_ids_path))

    @staticmethod
    def set_endpoint_formats(endpoints_config: Dict[str, str]) -> None:
        GolfCourse.BOOKING_ENDPOINT = endpoints_config['booking_timetable']
        GolfCourse.ADD_TO_CART_ENDPOINT = endpoints_config['add_tee_time_to_cart']
        GolfCourse.CHECKOUT_ENDPOINT = endpoints_config['checkout']

    def __str__(self) -> str:
        print_str: str = '\nName: ' + self.name + '\nId: ' + self._id \
            + '\nCache Path: ' + self._cache_path + '\nBooking Ids Path: ' + self._booking_ids_path \
            + '\nBaseUrl: ' + self._base_url + '\nLookahead Days: ' + str(self._lookahead_days)

        if self._round_types:
            print_str += '\nRound Types:\n\t'
            print_str += '\n\t'.join(str(x) for x in self._round_types.values())
            print_str += '\n'

        return print_str

    def get_new_tee_times(self, weekday_cut_time: datetime, weekend_cut_time: datetime, min_spots: int) -> Dict[str, Dict[date, List[TeeTimeGroup]]]:
        new_tee_times_by_round: Dict[str, Dict[date, List[TeeTimeGroup]]] = {}
        for round_type in self._round_types.values():
            print(f'Getting {round_type.name} Tee Times')
            new_tee_times_by_date: Dict[date, List[TeeTimeGroup]] = round_type.get_new_tee_times_for_period(weekday_cut_time, weekend_cut_time, min_spots, self._lookahead_days)
            if new_tee_times_by_date:
                new_tee_times_by_round[round_type.name] = new_tee_times_by_date
        self._save_to_json_to_path(self.serialize(), self._cache_path)
        self._save_to_json_to_path(self._get_booking_ids(), self._booking_ids_path)
        return new_tee_times_by_round

    def deserialize(self, tee_time_data: Any) -> None:
        for round_id, round_tee_time_data in tee_time_data.items():
            self._round_types[round_id].deserialize(round_tee_time_data)

    def serialize(self) -> Dict[str, Any]:
        tee_times: Dict[str, Any] = {}
        for round in self._round_types.values():
            round_data: Any = round.serialize()
            if round_data:
                tee_times[round.id] = round_data

        return tee_times

    def _set_booking_ids(self, new_booking_ids: Dict[str, Any]):
        for round_id, bookings_data in new_booking_ids.items():
            self._round_types[round_id].booking_ids = bookings_data

    def _get_booking_ids(self) -> Dict[str, Any]:
        booking_ids_by_round_type: Dict[str, Any] = {}
        for round_id, round in self._round_types.items():
            booking_ids_by_round_type[round_id] = round.booking_ids
        return booking_ids_by_round_type

    def _get_base_timetable_url(self) -> str:
        return self._base_url + GolfCourse.BOOKING_ENDPOINT.format(self._id, "{}", "{}")

    def _load_json_from_path(self, file_path: str) -> Any:
        if not os.path.exists(file_path) \
                or get_args().no_cache \
                or os.path.getsize(file_path) == 0:
            return {}

        with open(file_path, 'r') as f:
            return json.load(f)

    def _save_to_json_to_path(self, data: Any, file_path: str) -> None:
        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        with open(file_path, 'w') as f:
            json.dump(data, f)