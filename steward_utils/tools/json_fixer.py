from openai import OpenAI
from typing import Optional
import json
from ..configs import Config
from .utils import get_fn_args
import json_repair

class JsonFixer:
    """用于修复格式错误的JSON输出的工具类"""
    _instance = None
    
    def __new__(cls, config: Config = None, retry_times: int = 3):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Config = None, retry_times: int = 3):
        """
        初始化JSON修复器（单例模式）
        
        Args:
            config: 配置对象，仅在第一次初始化时使用
            retry_times: 重试次数，仅在第一次初始化时使用
        """
        if self._initialized:
            return
            
        if config is None:
            raise ValueError("首次初始化时必须提供config参数")
            
        openai_key = config.get_with_fallback("json_fixer.openai_key", "openai_api_key")
        openai_base = config.get_with_fallback("json_fixer.openai_base", "openai_api_base")
        model = config.get_with_fallback("json_fixer.model", "model")

        self.client = OpenAI(
            api_key=openai_key,
            base_url=openai_base
        )
        self.model = model
        self.retry_times = retry_times
        self._initialized = True

    def get_fn_args(self, fn_call: dict) -> dict|None:
        """
        解析函数调用参数，必要时使用LLM进行修复
        1. 先尝试使用get_fn_args解析
        2. 如果解析失败，则使用json_repair库进行修复
        3. 如果解析失败，使用LLM进行修复
        """
        args = get_fn_args(fn_call)
        if args is None:
            bad_json_str = str(fn_call['arguments'])
            good_json_str = json_repair.repair_json(bad_json_str)
            # If the string was super broken this will return an empty string
            if len(good_json_str) > 0:
                args = json.loads(good_json_str)
            else:
                args = None
        if args is None:
            args = self.fix_json_with_llm(fn_call['arguments'])
        return args

    def fix_json(self, broken_json: str, format_instructions: Optional[str] = None) -> str:
        """
        尝试修复格式错误的JSON字符串
        
        Args:
            broken_json: 需要修复的JSON字符串
            format_instructions: 可选的格式说明
            
        Returns:
            修复后的JSON字符串
        """
        if format_instructions is None:
            format_instructions = "请修复以下JSON字符串的格式错误，确保它是有效的JSON格式。请直接返回修复后的JSON字符串，不要返回任何其他内容。"
            
        prompt = f"{format_instructions}\n\n{broken_json}"
        for i in range(self.retry_times):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                {"role": "system", "content": "你是一个JSON修复专家。"},
                {"role": "user", "content": prompt}
                ]
            )
            json_str = response.choices[0].message.content.strip()
            if json_str.startswith("```json") and json_str.endswith("```"): # 有时候会脑抽，把json字符串包裹在```json```中
                json_str = json_str[7:-3].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"DEBUG - 修复失败: {json_str} 第{i+1}次尝试")
                continue
        return None
