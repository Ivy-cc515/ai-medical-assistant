RED_FLAG_KEYWORDS = [

    "胸痛",
    "胸悶",
    "呼吸困難",
    "喘不過氣",
    "低血壓",
    "心悸",
    "嚴重外傷",   # ← Bug 修正：原本缺少逗號，導致與下一行隱式串接

    "單側無力",
    "昏倒",
    "意識不清",
    "高燒不退",
    "急性劇烈腹痛",
    "突發性劇烈頭暈",
    "突發性劇烈眩暈",
    "突發性劇烈頭痛",  # ← Bug 修正：同上，原本缺少逗號

    "大量出血",
    "無法呼吸",
    "嚴重過敏反應",
    "大面積燒傷",
    "嚴重頭部受傷",
    "嚴重骨折",
    "氣喘發作",
]


def check_emergency(user_input: str) -> bool:
    """
    Gate 1：Red Flag Rule
    掃描使用者輸入是否包含緊急症狀關鍵字。
    """
    for keyword in RED_FLAG_KEYWORDS:
        if keyword in user_input:
            return True
    return False