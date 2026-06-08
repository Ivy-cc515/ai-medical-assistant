# ─────────────────────────────────────────
# 階段三-B：白話文確認摘要 Prompt
# ─────────────────────────────────────────
 
def build_confirmation_prompt(symptoms: list, duration: str, description: str) -> str:
    return f"""
你是一個親切的醫療問診助理，請將以下結構化資料轉換成一段「確認語句」。
 
資料：
- 症狀：{", ".join(symptoms)}
- 持續時間：{duration or "不確定"}
- 描述：{description or "無補充"}
 
要求：
- 用「幫您確認一下，您目前的狀況是...」開頭。
- 語氣口語、親切。
- 結尾加上「請問這樣正確嗎？」
- 只輸出純文字，不要 JSON 也不要 markdown。
"""
