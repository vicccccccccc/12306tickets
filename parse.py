# coding: utf-8


import re
from pprint import pprint


with open('stations.html', 'r', encoding='UTF-8') as f:
    text = f.read()
    stations = re.findall(u'([\u4e00-\u9fa5]+)\|([A-Z]+)', text)
    stations_dict = dict(stations)
    for key, value in stations_dict.items():
        _value = str(key.encode('unicode-escape'))
        _value = _value.replace("\\\\", "%")[2::]
        _value = _value.replace("'", "")
        _value += '%2C' + value
        stations_dict[key] = _value

    # pprint(dict(stations), indent=4)
    pprint(stations_dict, indent=4)

