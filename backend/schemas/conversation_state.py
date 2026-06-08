from pydantic import BaseModel
from typing import List, Optional

class ConversationState(BaseModel):

    # 階段一：症狀抽取結果
    symptoms: List[str] = []
    duration: Optional[str] = None
    description: Optional[str] = None

    # 階段二：追問狀態
    followup_count: int = 0
    MAX_FOLLOWUP: int = 2          # 追問上限，超過強制放行

    # 階段三：導診結果
    recommended_department: Optional[str] = None
    severity: Optional[str] = None
    triage_reason: Optional[str] = None
    triage_action: Optional[str] = None
    triage_advice: Optional[str] = None
    confirmation_summary: Optional[str] = None  # 白話文確認句
    awaiting_confirmation: bool = False

    # 階段四：診所資訊
    user_location: Optional[str] = None
    
    # ─────────────────────────────────────────────────────────
    # 新增 👉 階段五：掛號狀態與資料 (Appointment State)
    # ─────────────────────────────────────────────────────────
    triage_completed: bool = False      # 標記：前四階段是否已走完
    
    # AI 收集中的掛號參數
    appointment_date: Optional[str] = None  
    time_slot: Optional[str] = None         
    schedule_id: Optional[int] = None       
    patient_id: Optional[str] = None        
    birth: Optional[str] = None             
    visittype: Optional[str] = None         
    
    appointment_completed: bool = False # 標記：是否已經成功 call 完掛號 API
    # ─────────────────────────────────────────────────────────

    def is_info_complete(self) -> bool:
        """
        Gate 2 條件 A：核心三要素是否齊全
        symptoms + description + duration 皆有值才算完整
        """
        return (
            len(self.symptoms) > 0
            and bool(self.description)
            and bool(self.duration)
        )

    def should_stop_followup(self) -> bool:
        """
        Gate 2 停損判斷：
        - 條件 A：資訊完整
        - 條件 B：追問次數已達上限
        """
        return self.is_info_complete() or self.followup_count >= self.MAX_FOLLOWUP

    def missing_fields(self) -> List[str]:
        """回傳目前缺少哪些核心欄位，供 followup agent 決定追問方向"""
        missing = []
        if not self.symptoms:
            missing.append("symptoms")
        if not self.description:
            missing.append("description")
        if not self.duration:
            missing.append("duration")
        return missing