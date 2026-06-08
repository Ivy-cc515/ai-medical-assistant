const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ChatRequest {
  message: string;
  session_id?: string;
  user_location?: string;
}

export interface ClinicInfo {
  name: string;
  address: string;
  rating: number | string;
  open_now: boolean | null;
  maps_url: string;
}

export interface ChatResponse {
  // 🚨 [修改這裡] 加入 "appointment" 型別
  type: "invalid" | "emergency" | "followup" | "confirmation" | "result" | "appointment";
  message: string;
  action?: string;
  data?: {
    session_id?: string;
    followup_count?: number;
    missing_fields?: string[];
    triage?: {
      department: string;
      severity: string;
      reason: string;
    };
    structured_symptoms?: {
      symptoms: string[];
      duration: string;
      description: string;
    };
    nearby_clinics?: ClinicInfo[];
    state?: Record<string, unknown>;
  };
}

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  // 💡 小提醒：因為我們剛剛把 AI 後端改到了 8001 port，
  // 請確認你的 .env 檔或這裡的預設值是否也改成了 8001
  const targetUrl = API_BASE.includes("8000") ? "http://127.0.0.1:8001" : API_BASE;
  
  const res = await fetch(`${targetUrl}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}