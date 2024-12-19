import inspect
import os
from ..configs import Config
import importlib
from .json_fixer import JsonFixer
from time import strftime, localtime
from openai import OpenAI

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


STEWARD_LOG_LEVELS = {
    "debug": 0,
    "info": 1,
    "warning": 2,
    "error": 3,
}
STEWARD_LOG_LEVEL = "info"
STEWARD_LOG_DIR = ".local/tool_logs"
os.makedirs(STEWARD_LOG_DIR, exist_ok=True)

# 添加ToolMetaclass
class OmniToolMetaclass(type):
    registered_tools = {}  # 用于存储所有工具类

    def __new__(cls, name, bases, attrs):
        tool_class = super().__new__(cls, name, bases, attrs)
        if name not in ['OmniTool', 'OmniAgent']:  # 不记录基类
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
    # {key: config_key, default: default_value, required: bool, map_to: map_to_key}

    def __init__(self, config: Config, parent = None):
        self.__init_called = False
        self.config = config
        self.parent = parent
        # 自动化赋值
        for item in self.config_items:
            if item['required']:
                assert self.config.get(item['key'], None) is not None
            value = self.config.get(item['key'], item['default'])
            target_key = item.get('map_to', item['key'])
            setattr(self, target_key, value)
            print(f"{self.name} 的 {target_key} 自动设置为 {value}")

        self.__init_called = True
        self.init_time = strftime("%Y-%m-%d-%H-%M-%S", localtime())
        self.log_file = os.path.join(STEWARD_LOG_DIR, f"{self.name}-{self.init_time}.log")


    def __call__(self, **kwargs):
        raise NotImplementedError(f"{self.name} 未实现")
    
    def log(self, level: str, *args, **kwargs):
        if STEWARD_LOG_LEVELS[STEWARD_LOG_LEVEL] >= STEWARD_LOG_LEVELS[level]: # 如果日志级别大于等于当前级别，则打印
            print(f"[{self.name}] {level}", *args, **kwargs)

        with open(self.log_file, "a", encoding="utf-8") as f:
            print(f"[{self.name}] {level}", *args, **kwargs, file=f)

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


class OmniAgent(OmniTool):
    """
    特殊的工具类，它本身是一个工具，但是它能够调用其他工具
    所以它其实是Agent，待拓展
    """
    agent_api_key_sources = ['openai_api_key']
    agent_base_url_sources = ['openai_api_base']
    agent_model_sources = ['model']

    def __init__(self, config: Config):
        super().__init__(config)
        self.json_fixer = JsonFixer(config)
        self.client_api_key = config.get_with_fallback(*self.agent_api_key_sources)
        self.client_base_url = config.get_with_fallback(*self.agent_base_url_sources)
        self.client_model = config.get_with_fallback(*self.agent_model_sources)
        self.client = OpenAI(api_key=self.client_api_key, base_url=self.client_base_url)
        
        self.tools: list[OmniTool] = self.create_tools(config)
        self.name2fn = {tool.name: tool for tool in self.tools}
        santilized_model_name = self.client_model.replace('/', '_')
        self.log_file = self.log_file.replace('.log', f'-{santilized_model_name}.log')


    def create_tools(self, config: Config)->list[OmniTool]: # 创建工具
        raise NotImplementedError(f"{self.name} 未实现")

    def tools_json(self):
        return [tool.json() for tool in self.tools]

    def get_fn(self, fn_name):
        return self.name2fn[fn_name]
    
    def get_fn_args(self, fn_call: dict) -> dict| None:
        return self.json_fixer.get_fn_args(fn_call)
    
    def get_system_prompt(self):
        raise NotImplementedError(f"{self.name} 未实现")

    def __call__(self, query):
        system_prompt = self.get_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]
        self.log('debug', f"系统提示: {system_prompt}")
        response = self.client.chat.completions.create(
            model=self.client_model,
            messages=messages,
            tools=self.tools_json(),
        )
        
        message = response.choices[0].message.model_dump()
        self.log('debug', f"AI完整响应: {message}")
        content = message['content']
        tool_calls = message['tool_calls']
        if len(content) != 0:
            self.log('debug', f"AI回答: {content}")
            if tool_calls is None:
                return content
            else:
                return '没有执行任何操作'
        
        if tool_calls is None:
            return '没有执行任何操作'
            
        results = []
        for tool_call in tool_calls:
            fn_call = tool_call['function']
            fn_name = fn_call['name']
            fn = self.get_fn(fn_name)
            if fn is None:
                self.log('error', f"工具 {fn_name} 不存在")
                continue
            fn_args = self.get_fn_args(fn_call)
            if fn_args is None:
                self.log('error', f"解析参数失败: {fn_call['arguments']}")
                continue
            self.log('debug', f"调用参数: {fn_args}")
            result = fn(**fn_args)
            results.append(result)
            
        return '\n'.join(results) if results else '没有执行任何操作'
            

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