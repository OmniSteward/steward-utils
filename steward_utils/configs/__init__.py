
from types import ModuleType, FunctionType, SimpleNamespace
import json


class Config(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)
    
    def dump2json(self):
        sub_config = {}
        for key, value in self.__dict__.items():
            if isinstance(value, ModuleType) or isinstance(value, FunctionType) or isinstance(value, type):
                continue
            sub_config[key] = value
        return json.dumps(sub_config, indent=4, ensure_ascii=False)

def load_config_from_json(json_path: str):
    with open(json_path, 'r', encoding='utf-8') as file:
        config_dict = json.load(file)
    return Config(**config_dict)
