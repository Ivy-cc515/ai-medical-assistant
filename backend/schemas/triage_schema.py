from pydantic import BaseModel
from typing import Optional

class TriageResult(BaseModel):         
    department: str
    severity: str
    reason: str
    action: Optional[str] = None       # "self_care" | "clinic" | "emergency"
    advice: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None     # 用於多輪對話狀態追蹤
    user_location: Optional[str] = None  # 階段四：使用者所在行政區或座標


class ChatResponse(BaseModel):
    type: str        # "emergency" | "followup" | "confirmation" | "result"
    message: str
    data: Optional[dict] = None
    action: Optional[str] = None