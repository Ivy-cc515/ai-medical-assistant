import json

from prompts.followup_prompt import build_followup_prompt
from service.gemini_service import GeminiService
from schemas.conversation_state import ConversationState


class FollowupAgent:
    """
    階段二：智能追問
    根據 ConversationState 中缺少的欄位，
    生成一個最關鍵的追問問題。
    """

    def __init__(self):
        self.gemini = GeminiService()

    def generate_question(self, state: ConversationState) -> str:
        """
        回傳追問問題字串。
        若 Gemini 解析失敗，回傳預設問題。
        """
        missing = state.missing_fields()

        prompt = build_followup_prompt(
            missing_fields=missing,
            symptoms_so_far=state.symptoms,
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
            return data.get("question", self._default_question(missing))
        except json.JSONDecodeError:
            return self._default_question(missing)

    @staticmethod
    def _default_question(missing: list) -> str:
        fallbacks = {
            "symptoms":    "請問您目前有哪些不舒服的症狀？",
            "duration":    "請問這些症狀大概持續多久了？",
            "description": "請問症狀是持續的還是間歇性的？有沒有特別讓症狀加重的狀況？",
        }
        if missing:
            return fallbacks.get(missing[0], "請問還有其他不舒服的地方嗎？")
        return "請問還有其他想補充的嗎？"