from steward_utils.tools.json_fixer import JsonFixer
from steward_utils import load_config_from_json
import os

text = '{"entity_id": "switch.zhimi_cn_70779380_m2_on_p_2_1", "service": "turn_on", "data": {}'


if __name__ == "__main__":
    json_path = os.environ.get("JSON_PATH") 
    print(json_path)
    config = load_config_from_json(json_path)
    fixer = JsonFixer(api_key=config.openai_api_key, api_base=config.openai_api_base, model=config.model)
    print(fixer.fix_json(text))
