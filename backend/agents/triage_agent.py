import json

from prompts.triage_prompt import build_triage_prompt
from prompts.confirmation_prompt import build_confirmation_prompt
from service.gemini_service import GeminiService
from schemas.conversation_state import ConversationState


class TriageAgent:
    """
    階段三：確認與科別推薦
    - generate_confirmation()：生成白話文確認摘要（給使用者確認）
    - recommend()：根據症狀推薦科別，更新 state
    """

    def __init__(self):
        self.gemini = GeminiService()

    def generate_confirmation(self, state: ConversationState) -> str:
        """
        將 state 轉換為親切的白話文確認句，
        讓使用者確認資訊是否正確。
        """
        prompt = build_confirmation_prompt(
            symptoms=state.symptoms,
            duration=state.duration or "",
            description=state.description or "",
        )
        summary = self.gemini.generate(prompt).strip()
        state.confirmation_summary = summary
        return summary

    def recommend(self, state: ConversationState) -> ConversationState:
        """
        呼叫 Gemini 判斷科別、嚴重度與原因，
        並將結果寫入 state。
        """
        prompt = build_triage_prompt(
            symptoms=state.symptoms,
            duration=state.duration or "",
            description=state.description or "",
        )

        response = self.gemini.generate(prompt)

        cleaned = (
            response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        try:
            data = json.loads(cleaned)
            state.recommended_department = data.get("department", "一般內科")
            state.severity = data.get("severity", "未知")
            state.triage_reason = data.get("reason", "")
            state.triage_action = data.get("action", "clinic")   
            state.triage_advice = data.get("advice", "")         
        except json.JSONDecodeError:
            state.recommended_department = "一般內科"
            state.severity = "未知"
            state.triage_reason = "無法自動判斷，建議諮詢現場醫護人員"
            state.triage_action = "clinic"                        
            state.triage_advice = ""                              

        return state