import os
import json
import datetime
from time import mktime
from models.models import BaseModel
from google.appengine.ext import ndb
import pickle
class GameOnUtils(object):
    debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Development/')

    @classmethod
    def json_serializer(cls, obj):

        """Default JSON serializer."""
        import calendar, datetime

        if isinstance(obj, datetime.datetime):
            if obj.utcoffset() is not None:
                obj = obj - obj.utcoffset()
        millis = int(
            calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000
        )
        return millis

    class MyEncoder(json.JSONEncoder):

        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return int(mktime(obj.timetuple()))
            if isinstance(obj, BaseModel):
                obj.key = None
                obj.id = None
                return obj.to_dict()

            return obj.__dict__ #json.JSONEncoder.default(self, obj.__dict__)
