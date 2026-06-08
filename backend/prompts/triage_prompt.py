# ─────────────────────────────────────────
# 階段三-A：導診（科別推薦）Prompt
# ─────────────────────────────────────────
 
def build_triage_prompt(symptoms: list, duration: str, description: str) -> str:
    return f"""
你是一個 AI 導診系統，根據病患症狀給出分級建議。

病患資訊：
- 症狀：{", ".join(symptoms)}
- 持續時間：{duration or "未知"}
- 補充描述：{description or "無"}

請判斷並回傳以下欄位：
- department (str)    — 若需就醫，推薦科別（例如：內科、耳鼻喉科）
- severity   (str)    — 輕症 / 中度 / 重症
- action     (str)    — 建議行動，從以下三種選一：
                        "self_care"（居家觀察）
                        "clinic"（建議就診診所）
                        "emergency"（立即急診）
- advice     (str)    — 給使用者的具體建議，包含：
                        輕症：居家處理方式 + 幾天後若未改善再就醫
                        中度：建議盡快至診所就診
                        重症：立即就醫
- reason     (str)    — 一句話說明判斷原因

分級原則：
- 輕症（如輕微頭痛、輕微感冒）：先建議居家觀察或藥局購藥，說明幾天後未改善再就醫
- 中度（如持續發燒、較嚴重疼痛）：建議就近診所就診
- 重症（如劇烈疼痛、呼吸困難）：立即急診

只能輸出合法 JSON，不要加任何說明文字。

輸出格式：
{{
    "department": "",
    "severity": "",
    "action": "",
    "advice": "",
    "reason": ""
}}
"""