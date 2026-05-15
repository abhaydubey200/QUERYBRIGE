from typing import List, Dict

class MaskingService:
    def __init__(self):
        self.sensitive_keywords = ["email", "phone", "ssn", "password", "card", "salary", "revenue"]

    def apply_masking(self, data: List[Dict], user_role: str):
        """Redact sensitive columns for non-admin roles."""
        if user_role == "admin":
            return data

        masked_data = []
        for row in data:
            new_row = {}
            for col, val in row.items():
                if any(keyword in col.lower() for keyword in self.sensitive_keywords):
                    new_row[col] = self._redact(val)
                else:
                    new_row[col] = val
            masked_data.append(new_row)
        
        return masked_data

    def _redact(self, val):
        if val is None:
            return None
        s_val = str(val)
        if len(s_val) <= 4:
            return "****"
        return s_val[:2] + "*" * (len(s_val) - 4) + s_val[-2:]
