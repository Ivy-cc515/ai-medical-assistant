import json

from prompts.extraction_prompt import build_extraction_prompt
from service.gemini_service import GeminiService
from schemas.conversation_state import ConversationState


class IntakeAgent:
    """
    階段一：症狀抽取
    將使用者的自然語言輸入轉換為結構化 JSON，
    並更新 ConversationState。
    """

    def __init__(self):
        self.gemini = GeminiService()

    def extract(self, user_input: str, state: ConversationState) -> ConversationState:
        """
        呼叫 Gemini 抽取症狀、持續時間、描述，
        並將結果 merge 進現有的 state（支援多輪累積）。
        """
        prompt = build_extraction_prompt(user_input)
        response = self.gemini.generate(prompt)

        cleaned = (
            response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # 解析失敗時不更新 state，原樣返回
            return state

        # Merge：新抽取到的症狀附加到現有清單，避免多輪對話覆蓋
        new_symptoms = data.get("symptoms", [])
        if new_symptoms:
            existing = set(state.symptoms)
            for s in new_symptoms:
                if s not in existing:
                    state.symptoms.append(s)

        # duration / description：只在原本為空時才更新
        if not state.duration and data.get("duration"):
            state.duration = data["duration"]

        if not state.description and data.get("description"):
            state.description = data["description"]

        return state