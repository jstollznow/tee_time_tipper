from enum import Enum

class RoundTimeOfWeek(Enum):
    all = 0
    weekend = 1
    weekday = 2

class GolfRoundType:
    def __init__(self, round_type_config) -> None:
        self.id = round_type_config['id']
        self.name = round_type_config['name']
        self.type = RoundTimeOfWeek[round_type_config.get('type', 'all').lower()]

    def __str__(self):
        return str(vars(self))