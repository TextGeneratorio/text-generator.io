import json

from questions.example_fixtures import openai_examples
from questions.usecase_fixtures import use_cases


class Fixture(object):
    def __init__(self):
        super(Fixture, self).__init__()

    def to_JSON(self):
        # todo compress by removing nulls
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


# todo careful with global

_stop_reason = None


def set_stop_reason(stop_reason):
    global _stop_reason
    _stop_reason = stop_reason


def get_stop_reason():
    global _stop_reason
    return _stop_reason


# join openai examples
use_cases.update(openai_examples)
