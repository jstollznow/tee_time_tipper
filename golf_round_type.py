from enum import Enum


class GolfRoundType:
    def __init__(self, round_type_config) -> None:
        self.round_type_id = round_type_config['id']
        self.name = round_type_config['name']
        self.type = round_type_config['type']

    def __str__(self):
        # return 'Name: ' + self.name + ', Round Type Id: ' + self.round_type_id \
        #     + ', Round Type: ' + self.type
        return str(vars(self))