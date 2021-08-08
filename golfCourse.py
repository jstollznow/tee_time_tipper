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
    TAKEN = "Taken"

    def __init__(self, name, baseUrl, feeGroups) -> None:
        self.name = name
        self.file_name = f"./cache/{name.lower().replace(' ', '_')}.pickle"
        self.baseUrl = baseUrl
        self.roundTypes = feeGroups
        self.tee_times_by_date = self.__restore_times()

    def getNewTeeTimes(self, request_session, latest_tee_time, lookahead_days, min_spots):
        current_tee_times_by_date = {}
        new_tee_times_by_date = {}
        for _ in range(lookahead_days):
            current_tee_times = self.__getTeeTimes(request_session, latest_tee_time, min_spots)
            print(latest_tee_time.date())
            if (len(current_tee_times) > 0):
                current_tee_times_by_date[latest_tee_time.date()] = current_tee_times
                if not latest_tee_time.date() in self.tee_times_by_date:
                    new_tee_times_by_date[latest_tee_time.date()] = sorted(current_tee_times)
                else:
                    new_tee_times = current_tee_times - self.tee_times_by_date[latest_tee_time.date()]
                    if len(new_tee_times) > 0:
                        new_tee_times_by_date[latest_tee_time.date()] = sorted(new_tee_times)
            latest_tee_time += timedelta(days=1)
        self.__save_times(current_tee_times_by_date)
        return new_tee_times_by_date

    def __getTeeTimes(self, request_session, latest_tee_time, min_spots):
        tee_times = set()
        for id, name in self.roundTypes.items():
            soup = BeautifulSoup(self.__getContent(request_session, latest_tee_time, id), 'html.parser')
            for row in soup.find_all('div', {"class": "row row-time pm_row"}):
                if (self.__getSpotsAvailable(row)):
                    tee_time = self.__getTeeTime(row)
                    if (tee_time.time() < latest_tee_time.time()):
                        tee_times.add(tee_time.strftime('%I:%M %p'))
                
        return tee_times

    def __getContent(self, request_session, date, feeGroupId):
        url = f"{self.baseUrl}&selectedDate={date.year}-{date.month:02d}-{date.day:02d}&feeGroupId={feeGroupId}"
        return request_session.get(url).text

    def __isTeeTimeKnown(self, date, time_str):
        return date in self.tee_times_by_date and time_str in self.tee_times_by_date[date]

    def __sortedNewTeeTimes(self, date, currentTeeTimes):
        new_tee_times = self.tee_times_by_date[date].symmetric_difference_update(currentTeeTimes)
        if new_tee_times is not None:
            return sorted(new_tee_times)

        return new_tee_times

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
        if not os.path.exists(self.file_name):
            return {} 
        with open(self.file_name, 'rb') as f:
            return pickle.load(f)
        
    def __save_times(self, current_tee_times_by_date):
        if not os.path.exists(os.path.dirname(self.file_name)):
            try:
                os.makedirs(os.path.dirname(self.file_name))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        self.tee_times_by_date = current_tee_times_by_date
        with open(self.file_name, 'wb') as f:
            pickle.dump(self.tee_times_by_date, f)
