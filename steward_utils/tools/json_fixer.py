from openai import OpenAI
from typing import Optional
import json

class JsonFixer:
    """用于修复格式错误的JSON输出的工具类"""
    
    def __init__(self, api_key: str, api_base: str, model: str, retry_times: int = 3):
        """
        初始化JSON修复器
        
        Args:
            api_key: OpenAI API密钥
            api_base: OpenAI API基础URL
            model: 要使用的模型名称
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        self.model = model
        self.retry_times = retry_times

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
