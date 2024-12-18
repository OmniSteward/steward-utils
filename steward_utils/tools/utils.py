import json

def get_fn_args(fn_call: dict):
    try:
        arguments = fn_call["arguments"]
        # print(f"DEBUG - 原始参数: {arguments}, 长度: {len(arguments)}")        # 调试信息
        
        if isinstance(arguments, str):
            # 移除所有多余的转义
            clean_args = arguments.replace('\\"', '"').strip('"')
            try:
                new_args = json.loads(clean_args)
                # print(f"成功清理参数: {new_args}, 类型: {type(new_args)}")  # 调试信息
                return new_args
            except json.JSONDecodeError:
                print('解析清理后的参数失败，尝试解析原始参数')
                return json.loads(arguments)
        return arguments
    except Exception as e:
        print(f"DEBUG - 解析错误: {str(e)}")  # 调试信息
        return None
