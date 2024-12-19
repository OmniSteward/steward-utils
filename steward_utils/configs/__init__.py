
from types import ModuleType, FunctionType, SimpleNamespace
import json


class Config(SimpleNamespace):
    def get(self, key, default=None):
        conf = self
        items = key.split('.')
        for item in items:
            conf = getattr(conf, item, None)
            if conf is None:
                return default
        return conf
    
    def get_with_fallback(self, *keys):
        """
        按顺序从config中获取值，如果未找到，则返回None
        """
        for key in keys:
            value = self.get(key, None)
            if value is not None:
                return value
        raise ValueError(f"未找到{keys}中的任何一个")
    
    def dump2json(self):
        sub_config = {}
        for key, value in self.__dict__.items():
            if isinstance(value, ModuleType) or isinstance(value, FunctionType) or isinstance(value, type): # 跳过模块、函数、类型
                continue
            if isinstance(value, Config):
                sub_config[key] = value.dump2json()
            else:
                sub_config[key] = value
        return json.dumps(sub_config, indent=4, ensure_ascii=False)

def json2config(json_dict: dict):
    for key, value in json_dict.items():
        if isinstance(value, dict):
            json_dict[key] = json2config(value)
    return Config(**json_dict)

def load_config_from_json(json_path: str):
    with open(json_path, 'r', encoding='utf-8') as file:
        config_dict = json.load(file)
    return json2config(config_dict)
