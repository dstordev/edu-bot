from enum import IntEnum


class SurveyState(IntEnum):
    on_site = 1
    not_on_site = 2
    absent_for_a_good_reason = 3
