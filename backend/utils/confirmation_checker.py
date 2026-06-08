# utils/confirmation_checker.py
CONFIRM_KEYWORDS = ["對", "是", "正確", "沒錯", "確認", "OK", "ok", "好", "嗯", "對的", "是的"]
DENY_KEYWORDS = ["不對", "錯", "不是", "不正確", "不", "否", "有誤"]

def check_user_confirmation(text: str) -> bool:
    for kw in DENY_KEYWORDS:
        if kw in text:
            return False
    for kw in CONFIRM_KEYWORDS:
        if kw in text:
            return True
    return True  # 預設視為確認，避免卡住