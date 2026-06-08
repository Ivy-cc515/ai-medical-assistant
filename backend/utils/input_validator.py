OFF_TOPIC_KEYWORDS = [
    "天氣", "股票", "新聞", "食譜", "旅遊",
    "電影", "音樂", "遊戲", "程式", "寫程式",
    "翻譯", "數學", "歷史", "政治",
]

SYMPTOM_KEYWORDS = [
    "痛", "癢", "腫", "燒", "發燒", "咳嗽", "流鼻水",
    "頭暈", "噁心", "嘔吐", "疲勞", "無力", "不舒服",
    "症狀", "不適", "受傷", "流血", "過敏", "皮疹",
    "腹瀉", "便秘", "失眠", "焦慮", "憂鬱", "呼吸",
    "喘", "睡不好", "沒食慾", "體重",
]


def validate_input(text: str) -> dict:

    # 第一層：關鍵字規則（0 token）
    # 順序很重要：症狀檢查一定要在長度檢查之前
    if any(kw in text for kw in SYMPTOM_KEYWORDS):
        return {"valid": True}                          # 直接放行

    if len(text.strip()) < 3:
        return {"valid": False, "reason": "too_short"}  # 擋掉

    if any(kw in text for kw in OFF_TOPIC_KEYWORDS):
        return {"valid": False, "reason": "off_topic"}  # 擋掉

    # 第二層：交給 LLM 處理模糊地帶
    return {"valid": None, "reason": "needs_llm_check"}