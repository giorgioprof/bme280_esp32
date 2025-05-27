from machine import reset
import json
import os
from custom_exceptions import MissingConfig, InvalidConfig


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = AttrDict(value)
    
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"No attribute '{name}'")
    
    def validate(self, expected_attrs):
        try:
            for expected_attr in expected_attrs:
                splitted = expected_attr.split('__')
                res = self[splitted[0]]
                for x in splitted[1:]:
                    res = res[x]
        except KeyError as ex:
            print('Missing key:', ex)
            return False
        return True
    
class Config:
    expected_attrs = (
        'wifi__ssid',
        'wifi__password',
        'device__name',
        'mqtt__broker',
        'mqtt__port',
        'mqtt__username',
        'mqtt__password',
        'mqtt__topic',
        'readings__sleep',
        'readings__number'
    )

    def __init__(self, config_file, config_dict=None):
        self.config_file = config_file
        if not self.config_file_exists:
            if config_dict:
                self.config = AttrDict(config_dict)
                if not self.config.validate(self.expected_attrs):
                    raise InvalidConfig
                with open(self.config_file, 'w') as f:                    
                    f.write(json.dumps(config_dict))
            else:
                raise MissingConfig
        else:
            with open(self.config_file, 'r') as f:
                try:
                    self.config = AttrDict(json.loads(f.read()))
                except ValueError:
                    os.remove(config_file)
                    raise MissingConfig
            
    @property
    def config_file_exists(self):
        try:
            os.stat(self.config_file)
            return True
        except OSError:
            return False
    
    def reset(self):
        os.remove(self.config_file)
        reset()
    
    