import json

"""
code taken from https://stackoverflow.com/questions/4723535/how-to-decode-json-to-str-and-not-unicode-in-python-2-6
"""

from _json import scanstring as c_scanstring
from json import decoder, scanner
_CONSTANTS = json.decoder._CONSTANTS

py_make_scanner = scanner.py_make_scanner

def str_scanstring(*args, **kwargs):
    result = c_scanstring(*args, **kwargs)
    return str(result[0]), result[1]

class MyJSONDecoder(json.JSONDecoder):
    def __init__(self, encoding=None, object_hook=None, parse_float=None,
            parse_int=None, parse_constant=None, strict=True,
            object_pairs_hook=None):
        self.encoding = encoding
        self.object_hook = object_hook
        self.object_pairs_hook = object_pairs_hook
        self.parse_float = parse_float or float
        self.parse_int = parse_int or int
        self.parse_constant = parse_constant or _CONSTANTS.__getitem__
        self.strict = strict
        self.parse_object = decoder.JSONObject
        self.parse_array = decoder.JSONArray
        self.parse_string = str_scanstring
        self.scan_once = py_make_scanner(self)

def json_load(raw):
   raw_data = json.load(raw)
   data = dict()
   for (k,v) in raw_data.iteritems():
      print k, type(k)
      if type(v) == unicode:
         v = str(v)

      data[str(k)] = v
   return data


