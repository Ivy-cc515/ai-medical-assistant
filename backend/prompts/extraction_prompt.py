# ─────────────────────────────────────────
# 階段一：症狀抽取 Prompt
# ─────────────────────────────────────────
 
def build_extraction_prompt(user_input: str) -> str:
    return f"""
你是一個 AI Intake Assistant，負責從病患描述中抽取結構化資訊。
 
請從以下使用者輸入中抽取三個欄位：
1. symptoms  (list)  — 所有症狀，每個症狀為獨立字串
2. duration  (str)   — 持續時間，若未提及則為空字串 ""
3. description (str) — 症狀的補充描述（嚴重度、伴隨狀況等），若未提及則為空字串 ""
 
規則：
- 只輸出合法 JSON，不要加任何說明文字或 markdown。
- 若某欄位資訊不足，回傳空值（[] 或 ""），不要捏造。
 
輸出格式：
{{
    "symptoms": [],
    "duration": "",
    "description": ""
}}
 
使用者輸入：
{user_input}
"""