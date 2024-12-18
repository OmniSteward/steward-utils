import inspect
import os
from configs import Config
import json
import importlib

current_os = os.name
if current_os == "nt":
    current_os = "windows"
elif current_os == "posix":
    current_os = "linux"
elif current_os == "mac":
    current_os = "macos"

class OmniToolResult:
    ignore_keys = ["is_tool_result", "action"]
    def __init__(self, status: str, content: str, action: dict = None, is_tool_result: bool = True):
        self.status = status
        self.content = content
        self.action = action
        self.is_tool_result = is_tool_result

    def __str__(self):
        return str({k:v for k,v in self.__dict__.items() if k not in self.ignore_keys})
    
    def to_dict(self):
        return {k:v for k,v in self.__dict__.items()}


# 添加ToolMetaclass
class OmniToolMetaclass(type):
    registered_tools = {}  # 用于存储所有工具类
    
    def __new__(cls, name, bases, attrs):
        tool_class = super().__new__(cls, name, bases, attrs)
        if name != 'OmniTool':  # 不记录基类Tool
            cls.registered_tools[tool_class.name] = tool_class
        return tool_class


class OmniTool(metaclass=OmniToolMetaclass):
    """
    工具类，用于定义工具，
    能够自动生成json格式，用于LLM调用
    """
    name: str
    description: str
    parameters: dict = {
        "param": {
            "type": "string",
            "description": "参数描述",
        }
    }
    support_os = ["windows", "linux", "macos"]
    config_items = []
    # {key: config_key, default: default_value, required: bool}

    def __init__(self, config: Config):
        self.__init_called = False
        self.config = config
        # 自动化赋值
        for item in self.config_items:
            if item['required']:
                assert hasattr(self.config, item['key']), f"{item['key']} 未在配置中指定"
            value = getattr(self.config, item['key'], item['default'])
            setattr(self, item['key'], value) # 设置属性
            print(f"{self.name} 的 {item['key']} 自动设置为 {value}")

        self.__init_called = True


    def __call__(self, **kwargs):
        raise NotImplementedError(f"{self.name} 未实现")

    # 将静态方法改为类方法
    @classmethod
    def is_supported(cls):
        return current_os in cls.support_os

    def json(self): # 返回json格式, 用于LLM调用
        if not self.__init_called:
            raise ValueError(f"{self.name} 未调用__init__方法")
        if current_os not in self.support_os:
            raise ValueError(f"当前操作系统 {current_os} 不支持该工具, 请在{self.support_os}中选择一个")
        parameters = inspect.signature(self.__call__).parameters
        required_parameter_names = []
        for param_name, param in parameters.items(): # 通过inspect获取参数名，判断是否需要传入
            if param.default == inspect._empty: # 没有默认值
                required_parameter_names.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": required_parameter_names,
                }
            }
        }
    
    def __call__(self, *args, **kwargs):
        raise NotImplementedError(f"{self.name} 未实现")


def get_omni_tool_class(tool_name):
    if '.' in tool_name: # 说明tool还未导入 steward.tools.hello.Hello
        module_name, class_name = tool_name.rsplit('.', 1)
        try:
            module = importlib.import_module(module_name)
            tool_class = getattr(module, class_name)
            tool_name = tool_class.name
        except Exception as e:
            print(f"ERROR - 导入OmniTool类失败: {e}")
            raise e

    return tool_name, OmniToolMetaclass.registered_tools[tool_name]