import json
from service.gemini_service import GeminiService

_gemini = GeminiService()


def llm_check_relevance(text: str) -> bool:

    prompt = f"""
判斷以下輸入是否與「身體症狀或就醫需求」有關。

輸入：{text}

只能回傳 JSON，不要加任何說明：
{{"relevant": true}} 或 {{"relevant": false}}
"""
    try:
        response = _gemini.generate(prompt)
        cleaned = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        return data.get("relevant", False)
    except Exception:
        return True  # 解析失敗時放行，避免誤擋真實症狀