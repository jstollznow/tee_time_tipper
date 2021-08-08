from bs4 import BeautifulSoup
from datetime import timedelta, datetime
import pickle
import os
import errno

class GolfCourse:
    ROW_HEADING = "col-lg-8 col-md-4 col-sm-4 col-xs-4 row-heading"
    ROW_WRAPPER = "row"
    ROW_WRAPPER_TIME = "col-lg-6 col-md-6 col-sm-6 col-xs-6 row-heading-inner time-wrapper"
    TIME_HEADING = "h3"
    RECORDS_WRAPPER = "records-wrapper"
    AVAILABLE = "Available"

    def __init__(self, name, baseUrl, feeGroups) -> None:
        self.name = name
        self.__file_name = f"./cache/{name.lower().replace(' ', '_')}.pickle"
        self.tee_times_by_date = self.__restore_times()
        self.__baseUrl = baseUrl
        self.__roundTypes = feeGroups

    def getNewTeeTimes(self, request_session, latest_tee_time, lookahead_days, min_spots):
        current_tee_times_by_round = {}
        new_tee_times_by_round = {}
        for (round_id, round_name) in self.__roundTypes.items():
            print(f'Getting {round_name} Tee Times')
            (current_tee_times_by_date, new_tee_times_by_date) = self.__getTeeTimesForRoundType(round_name, round_id, request_session, latest_tee_time, min_spots, lookahead_days)
            if len(current_tee_times_by_date) != 0:
                current_tee_times_by_round[round_name] = current_tee_times_by_date
            if len(new_tee_times_by_date) != 0:
                new_tee_times_by_round[round_name] = new_tee_times_by_date
        self.__save_times(current_tee_times_by_round)
        return new_tee_times_by_round

    def __getTeeTimesForRoundType(self, round_name, round_id, request_session, latest_tee_time, min_spots, lookahead_days):
        current_tee_times_by_date = {}
        new_tee_times_by_date = {}
        for _ in range(lookahead_days):
            current_round_tee_times = self.__getTeeTimes(request_session, latest_tee_time, min_spots, round_id)
            if (len(current_round_tee_times) > 0):
                current_tee_times_by_date[latest_tee_time.date()] = current_round_tee_times
                if not round_name in self.tee_times_by_date or not latest_tee_time.date() in self.tee_times_by_date[round_name]:
                    new_tee_times_by_date[latest_tee_time.date()] = sorted(current_round_tee_times)
                else:
                    new_tee_times = current_round_tee_times - self.tee_times_by_date[round_name][latest_tee_time.date()]
                    if len(new_tee_times) > 0:
                        new_tee_times_by_date[latest_tee_time.date()] = sorted(new_tee_times)
            latest_tee_time += timedelta(days=1)

        return (current_tee_times_by_date, new_tee_times_by_date)

    def __getTeeTimes(self, request_session, latest_tee_time, min_spots, round_id):
        tee_times = set()
        soup = BeautifulSoup(self.__getContent(request_session, latest_tee_time, round_id), 'html.parser')
        for row in soup.find_all('div', {"class": "row row-time pm_row"}):
            if (self.__getSpotsAvailable(row) >= min_spots):
                tee_time = self.__getTeeTime(row)
                if (tee_time.time() <= latest_tee_time.time()):
                    tee_times.add(tee_time.strftime('%I:%M %p'))
                
        return tee_times

    def __getUrl(self, date, feeGroupId):
        return f"{self.__baseUrl}&selectedDate={date.year}-{date.month:02d}-{date.day:02d}&feeGroupId={feeGroupId}"

    def __getContent(self, request_session, date, feeGroupId):
        url = self.__getUrl(date, feeGroupId)
        return request_session.get(url).text

    def __getTeeTime(self, row):
        timeDiv = row.find("div", {"class": self.ROW_HEADING}).find('div', {"class": self.ROW_WRAPPER}).find('div', {"class": self.ROW_WRAPPER_TIME})
        return datetime.strptime(timeDiv.find(self.TIME_HEADING).text.strip(), '%I:%M %p')

    def __getSpotsAvailable(self, row):
        spotsAvailable = 0
        for spot in row.find("div", {"class": self.RECORDS_WRAPPER}).find_all('div'):
            if spot.text.strip() == self.AVAILABLE:
                spotsAvailable += 1
        
        return spotsAvailable

    def __restore_times(self):
        if not os.path.exists(self.__file_name):
            return {} 
        with open(self.__file_name, 'rb') as f:
            return pickle.load(f)
        
    def __save_times(self, current_tee_times_by_date):
        if not os.path.exists(os.path.dirname(self.__file_name)):
            try:
                os.makedirs(os.path.dirname(self.__file_name))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        self.tee_times_by_date = current_tee_times_by_date
        with open(self.__file_name, 'wb') as f:
            pickle.dump(self.tee_times_by_date, f)
