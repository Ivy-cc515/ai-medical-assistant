import requests
from google.genai import types
from service.gemini_service import GeminiService
from prompts.appointment_prompt import build_appointment_prompt
from schemas.conversation_state import ConversationState
# ──🚨 [記得匯入] 用來儲存狀態的工具 ──────────────────────────
from utils import session_store 

class AppointmentAgent:
    def __init__(self):
        self.gemini = GeminiService()
        # 暫存使用者的 chat session (因為掛號需要來回對話，用來暫存每個使用者的對話歷史)
        self.active_chats = {}

    def chat(self, user_input: str, session_id: str, state: ConversationState) -> str:
        """
        處理掛號階段的對話。
        """

        # ── 🎯 Tool 1：查班表（搬進 chat 內部） ───────────────────
        def fetch_hospital_schedules(department_name: str, appointment_date: str, time_slot: str) -> str:
            """
            當收集到使用者想看診的科別、日期與時段後，呼叫此工具查詢是否有醫生。
            參數：
            - department_name: 科別名稱，例如 "內科" 或 "耳鼻喉科"
            - appointment_date: 預計看診日期，格式 YYYY-MM-DD
            - time_slot: 時段，必須是 "上午" 或 "下午"
            """
            url = "http://127.0.0.1:8000/schedules/doctors/"
            params = {"department_name": department_name, "appointment_date": appointment_date, "time_slot": time_slot}
            
            try:
                res = requests.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    if not data:
                        return f"{appointment_date} {time_slot} 的 {department_name} 目前沒有可預約的醫生。"
                    return f"查到以下醫生資料：{data}。請向使用者報告名單，並詢問要掛哪一位，同時索取身分證與生日。"
                return "醫院系統查詢失敗，請稍後再試。"
            except requests.exceptions.ConnectionError:
                return "無法連線到醫院系統。"

        # ── 🎯 Tool 2：遠端掛號（搬進 chat 內部，核心修正點！） ──────
        def trigger_remote_appointment(birth: str, patient_id: str, visittype: str, schedule_id: int, appointment_date: str) -> str:
            """
            當使用者確定要掛號，且你已經收集齊全 [生日、身分證、初/複診、醫生班表代碼] 時，呼叫此工具執行掛號寫入。
            """
            url = "http://127.0.0.1:8000/appointments/"
            payload = {
                "birth": birth,
                "patient_id": patient_id.upper(),
                "visittype": visittype,
                "schedule_id": schedule_id,
                "appointment_date": appointment_date
            }
            try:
                res = requests.post(url, json=payload)
                if res.status_code == 200:
                    # 💡【核心修復】：因為在 chat 內部，這裡可以直接改寫外部傳進來的 state！
                    state.appointment_completed = True
                    session_store.save(session_id, state)  # 儲存回 session store
                    return "遠端掛號成功！已成功寫入醫院資料庫。請向使用者回報預約已完成，並親切道別。"
                else:
                    return f"醫院系統退回掛號請求：{res.text}"
            except requests.exceptions.ConnectionError:
                return "無法連線到醫院掛號系統。"

        # 將這一輪綁定了當前 state 的工具打包
        current_tools = [fetch_hospital_schedules, trigger_remote_appointment]

        # 如果這是此 session_id 第一次進入掛號流程，初始化一個帶有新工具箱的 Chat Session
        if session_id not in self.active_chats:
            chat_session = self.gemini.create_chat_session(tools=current_tools)
            
            # 寫入 System Prompt，定調它的掛號助理身分與規則
            system_prompt = build_appointment_prompt(
                department=state.recommended_department, 
                user_input=user_input
            )
            self.active_chats[session_id] = chat_session
            
            # 把 System Prompt 送給 AI，拿到第一句回覆
            response = chat_session.send_message(system_prompt)
            
        # 使用者已經在掛號流程中了（例如正在回報身分證）    
        else:
            chat_session = self.active_chats[session_id]
            # 即使是延續既有對話，Gemini 在觸發 Tool 時，依然會執行上面這兩個能修改 state 的新工具
            response = chat_session.send_message(user_input)
            
        return response.text