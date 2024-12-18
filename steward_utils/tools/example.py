from .base import OmniTool

class ListAllTools(OmniTool): # 继承就会自动注册
    """
    一个示例工具，它会把当前启用的工具列表打印出来
    """
    name = "list_all_tools" # 工具名，要添加到tool_names列表中的关键字
    description = "打印当前启用的工具列表"
    parameters = {
        "format": {
            "type": "boolean",
            "description": "是否格式化输出"
        }
    }
    support_os = ["windows", "linux", "macos"]  # 支持的系统

    # 配置项，用于自动赋值
    config_items = [
        {'key': 'tool_names', 'default': None, 'required': True},
    ] # 自动映射config.tool_names到self.tool_names

    def __call__(self, format: bool = False):
        if format:
            from pprint import pprint
            pprint(self.tool_names)
            return f"当前启用的工具列表: {self.tool_names}"
        else:
            print(self.tool_names)
            return f"当前启用的工具列表: {self.tool_names}"
