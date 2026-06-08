import uuid

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from schemas.triage_schema import ChatRequest, ChatResponse
from agents.intake_agent import IntakeAgent
from agents.followup_agent import FollowupAgent
from agents.triage_agent import TriageAgent

from agents.appointment_agent import AppointmentAgent
from service.clinic_service import ClinicService
from utils.safety_rules import check_emergency
from utils import session_store
from utils.input_validator import validate_input
from utils.llm_validator import llm_check_relevance
from utils.confirmation_checker import check_user_confirmation

app = FastAPI(title="AI Intake & Appointment Assistant API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # 預防萬一 Port 被佔用跳號
        "http://127.0.0.1:3001",
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 執行實例化
intake_agent = IntakeAgent()
followup_agent = FollowupAgent()
triage_agent = TriageAgent()
clinic_service = ClinicService()
Appointment_agent = AppointmentAgent()

@app.get("/")
def root():
    return {"message": "AI Assistant API is running."}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    # ── Session 管理 ──────────────────────────────────────────────
    session_id = req.session_id or str(uuid.uuid4())
    state = session_store.get_or_create(session_id)

    print(f"[DEBUG] req.session_id={req.session_id}")
    print(f"[DEBUG] awaiting_confirmation={state.awaiting_confirmation}")
    print(f"[DEBUG] confirmation_summary={state.confirmation_summary}")

    if req.user_location:
        state.user_location = req.user_location

    #── Gate 0｜自動掛號對話分流 (Appointment Routing)──────────────
    if state.triage_completed:
        # 防呆：如果掛號已經完成了，直接回傳結束語句
        session_store.clear(session_id)
        return ChatResponse(type="result", message="您的掛號手續已完成，祝您早日康復！")
    
        # 呼叫掛號 Agent 處理後續的多輪掛號對話 (喬時間、要個資、呼叫外部掛號 API)
        ai_replay = Appointment_agent.chat(req.message, session_id, state)

        # 重新撈取最新的 state，確認 AI 是否在剛才的對話中觸發了「掛號成功」工具
        state = session_store.get_or_create(session_id)

        if state.appointment_completed:
            # 掛號成功！清除對話紀錄，功成身退
            session_store.clear(session_id)
            return ChatResponse(
                type="result", 
                message=ai_reply,
                data={"session_id": session_id}
            )

        #  還在來回詢問個資中，維持 "appointment" 型別讓前端 React 知道要繼續對話
        return ChatResponse(
            type="appointment",
            message=ai_reply,
            data={"session_id": session_id}
        )
    
    # ── Gate 0.5｜輸入驗證（等待確認時跳過）────────────────────────
    if not state.awaiting_confirmation:
        validation = validate_input(req.message)

        if validation["valid"] is False:
            reason = validation["reason"]
            
            # 🚨 [修復 Bug] 追問階段允許簡短回答
            # 如果已經有收集到症狀 (len > 0)，代表正在一問一答，放行短句 (如「還好」)
            if reason == "too_short" and len(state.symptoms) > 0:
                pass  # 繞過攔截，繼續往下走
            else:
                msg = "請描述您的症狀，例如：「我頭痛已經兩天了」" if reason == "too_short" else "您好，我是醫療問診助理，請描述您目前的身體症狀。"
                return ChatResponse(type="invalid", message=msg)

        if validation["valid"] is None:
            # 🚨 [修復 Bug] 放寬追問階段的語意檢查
            # 只有在第一輪 (還沒症狀時)，才需要用 LLM 嚴格檢查是否偏離醫療主題
            if len(state.symptoms) == 0 and not llm_check_relevance(req.message):
                return ChatResponse(
                    type="invalid",
                    message="您好，我是醫療問診助理，請描述您目前的身體症狀。"
                )
            
    # ═══════════════════════════════════════════════════════════════
    # Gate 1｜緊急安全攔截 (Red Flag Rule)
    # ═══════════════════════════════════════════════════════════════
    if check_emergency(req.message):
        session_store.clear(session_id)
        return ChatResponse(
            type="emergency",
            message="⚠️ 偵測到可能的緊急症狀，請立即撥打 119 或前往最近的急診室。",
            action="trigger_emergency_alert",
            data={"session_id": session_id},
        )

    # ── 症狀抽取：將本輪輸入 merge 進 state ────────────────────────
    state = intake_agent.extract(req.message, state)
    session_store.save(session_id, state)

    # ═══════════════════════════════════════════════════════════════
    # Gate 2｜智能追問 / 停損放行
    # ═══════════════════════════════════════════════════════════════
    if not state.should_stop_followup():
        question = followup_agent.generate_question(state)
        state.followup_count += 1
        session_store.save(session_id, state)

        return ChatResponse(
            type="followup",
            message=question,
            data={
                "session_id": session_id,
                "followup_count": state.followup_count,
                "missing_fields": state.missing_fields(),
            },
        )

    # ═══════════════════════════════════════════════════════════════
    # 階段三-A：白話文確認摘要（第一次到達此步驟時觸發）
    # ═══════════════════════════════════════════════════════════════
    if not state.confirmation_summary:
        summary = triage_agent.generate_confirmation(state)
        state.awaiting_confirmation = True
        session_store.save(session_id, state)
        return ChatResponse(
            type="confirmation",
            message=summary,
            data={"session_id": session_id},
        )

    # ═══════════════════════════════════════════════════════════════
    # 階段三-B：使用者正在回答確認問題
    # ═══════════════════════════════════════════════════════════════
    if state.awaiting_confirmation:
        is_confirmed = check_user_confirmation(req.message)

        if is_confirmed:
            state.awaiting_confirmation = False
            state = triage_agent.recommend(state)
            session_store.save(session_id, state)
        else:
            state.confirmation_summary = None
            state.awaiting_confirmation = False
            state.symptoms = []
            state.duration = None
            state.description = None
            state.followup_count = 0
            session_store.save(session_id, state)
            return ChatResponse(
                type="followup",
                message="沒關係，請重新描述您的症狀，我重新幫您整理。",
                data={"session_id": session_id},
            )

    # ═══════════════════════════════════════════════════════════════
    # 階段四：找附近診所/醫院
    # ═══════════════════════════════════════════════════════════════
    clinics = []
    if state.user_location and state.recommended_department:
        clinics = clinic_service.find_nearby_clinics(
            department=state.recommended_department,
            location=state.user_location,
        )

    # ═══════════════════════════════════════════════════════════════
    # 階段五:交接與 Session 結束控制
    # ═══════════════════════════════════════════════════════════════
    # 如果導診建議是去實體診所/醫院，我們啟動掛號銜接，【不清除】Session 
    if state.triage_action == "clinic":
        state.triage_completed = True
        session_store.save(session_id, state)
        extra_message = "\n\n請問需要我協助您線上預約掛號嗎？"
    else:
        # 如果是 self_care（輕症居家觀察）或 emergency（重症），不需要掛號，直接清除 Session
        session_store.clear(session_id)
        extra_message = ""

    return ChatResponse(
        type="result",
        message=(
            f"根據您的症狀，建議前往【{state.recommended_department}】就診。"
            f"（嚴重程度：{state.severity}）{extra_message}"
        ),
        data={
            "session_id": session_id, # 必須回傳，讓前端下一輪對話可以帶回來
            "triage": {
                "department": state.recommended_department,
                "severity": state.severity,
                "reason": state.triage_reason,
                "action": state.triage_action,
                "advice": state.triage_advice,
            },
            "structured_symptoms": {
                "symptoms": state.symptoms,
                "duration": state.duration,
                "description": state.description,
            },
            "nearby_clinics": clinics,
        },
    )
