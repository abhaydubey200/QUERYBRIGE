import json
import re
from typing import Dict, Any, Optional
from loguru import logger

class AIJsonRecovery:
    """
    Recovers valid JSON from malformed LLM responses using regex and cleaning.
    """
    @staticmethod
    def extract_json(content: str) -> Optional[Dict[str, Any]]:
        try:
            # 1. Try direct parsing
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # 2. Try extracting from markdown blocks
                match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
                
                # 3. Try finding the first '{' and last '}'
                match = re.search(r"(\{.*\})", content, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
            except Exception as e:
                logger.error(f"JSON Recovery failed: {str(e)}")
        
        return None
