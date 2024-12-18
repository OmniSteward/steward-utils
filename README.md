
![OmniSteward 全能管家](https://raw.githubusercontent.com/OmniSteward/OmniSteward/refs/heads/main/assets/logo.png)

# Steward Utils 管家工具包

[全能管家(Omni-Steward)](https://github.com/OmniSteward/OmniSteward)工具包，包含各种实用工具，能够轻松扩展和实现自己的工具

## 安装

```bash
pip install git+https://github.com/OmniSteward/steward-utils.git
```

## 使用

### 1. 创建工具

```python
from steward_utils import OmniTool

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
            pprint(self.tool_names) # 因为self.tool_names已经被自动赋值，所以可以直接使用
            return f"当前启用的工具列表: {self.tool_names}"
        else:
            print(self.tool_names)
            return f"当前启用的工具列表: {self.tool_names}"
```
详细请参考[steward_utils/tools/example.py](steward_utils/tools/example.py)

### 2. 在Omni-Steward中注册使用工具
然后我们可以在Omni-Steward `Config` 中添加该工具，可以使用全路径，也可以使用name

1. 无需导入，直接使用全路径
```python
# 使用全路径
tool_names.append('steward_utils.tools.example.ListAllTools')
```
2. 导入后使用name
```python
from steward_utils.tools.example import ListAllTools # 导入工具
tool_names.append('list_all_tools') # 添加到工具列表
```
## 可用工具链接
- [Omni-HA: 通过自然语言控制Home Assistant](https://github.com/OmniSteward/Omni-HA)
