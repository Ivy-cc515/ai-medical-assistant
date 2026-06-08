"use client";

import { useState, useRef, useEffect } from "react";
import { sendChat, ChatResponse, ClinicInfo } from "@/lib/api";

// ─── 訊息型別 ────────────────────────────────────────────
type MessageRole = "user" | "ai";

interface Message {
  role: MessageRole;
  content: string;
  type?: ChatResponse["type"];
  clinics?: ClinicInfo[];
  triage?: {
    department: string;
    severity: string;
    reason: string;
  };
}

// ─── 嚴重程度顏色 ────────────────────────────────────────
const severityColor: Record<string, string> = {
  輕症: "bg-emerald-50 text-emerald-700 border-emerald-200",
  中度: "bg-amber-50 text-amber-700 border-amber-200",
  重症: "bg-rose-50 text-rose-700 border-rose-200",
};

// ─── 診所卡片 ─────────────────────────────────────────────
function ClinicCard({ clinic }: { clinic: ClinicInfo }) {
  return (
    <a
      href={clinic.maps_url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-white border border-slate-100 rounded-xl p-3 hover:border-slate-300 hover:shadow-sm transition-all duration-200"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-800 truncate">
            {clinic.name}
          </p>
          <p className="text-xs text-slate-400 mt-0.5 truncate">
            {clinic.address}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {clinic.rating !== "N/A" && (
            <span className="text-xs text-amber-500 font-medium">
              ★ {clinic.rating}
            </span>
          )}
          <span
            className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${
              clinic.open_now === true
                ? "bg-emerald-50 text-emerald-600"
                : clinic.open_now === false
                ? "bg-slate-100 text-slate-400"
                : "bg-slate-50 text-slate-400"
            }`}
          >
            {clinic.open_now === true
              ? "營業中"
              : clinic.open_now === false
              ? "已休診"
              : "未知"}
          </span>
        </div>
      </div>
      {clinic.maps_url && (
        <p className="text-xs text-sky-500 mt-1.5 flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          在 Google Maps 查看
        </p>
      )}
    </a>
  );
}

// ─── 訊息泡泡 ─────────────────────────────────────────────
function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[80%] space-y-2 ${isUser ? "items-end" : "items-start"} flex flex-col`}>

        {/* 主要文字泡泡 */}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? "bg-sky-500 text-white rounded-br-md"
              : msg.type === "followup"
              ? "bg-violet-50 text-slate-700 border border-violet-100 rounded-bl-md"
              : msg.type === "confirmation"
              ? "bg-sky-50 text-slate-700 border border-sky-100 rounded-bl-md"
              : msg.type === "appointment"  // 🚨 [修改] 新增掛號專屬的對話泡泡樣式
              ? "bg-teal-50 text-slate-700 border border-teal-100 rounded-bl-md"
              : "bg-slate-100 text-slate-700 rounded-bl-md"
          }`}
        >
          {msg.content}
        </div>

        {/* 導診結果 */}
        {msg.triage && (
          <div className="bg-white border border-slate-100 rounded-xl p-3 w-full space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">建議科別</span>
              <span className="text-sm font-semibold text-slate-800">
                {msg.triage.department}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
                  severityColor[msg.triage.severity] ?? "bg-slate-50 text-slate-500 border-slate-200"
                }`}
              >
                {msg.triage.severity}
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              {msg.triage.reason}
            </p>
          </div>
        )}

        {/* 診所列表 */}
        {msg.clinics && msg.clinics.length > 0 && (
          <div className="w-full space-y-2">
            <p className="text-xs text-slate-400 px-1">附近診所</p>
            {msg.clinics.map((c, i) => (
              <ClinicCard key={i} clinic={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── 主元件 ───────────────────────────────────────────────
export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "ai",
      content: "您好，我是 AI 醫療問診助理。請描述您目前的身體症狀，我來協助您找到合適的科別。",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [isEmergency, setIsEmergency] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 自動捲到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setInput("");

    // 加入使用者訊息
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setIsLoading(true);

    try {
      const res = await sendChat({
        message: userText,
        session_id: sessionId,
      });
      
      // 🚨 [保留] 記住 session_id，因為掛號需要好幾輪對話
      if (res.data?.session_id) {
        setSessionId(res.data.session_id);
      }

      // 緊急狀況：觸發全螢幕警告
      if (res.type === "emergency") {
        setIsEmergency(true);
        return;
      }

      // 組裝 AI 訊息
      const aiMessage: Message = {
        role: "ai",
        content: res.message,
        type: res.type,
        triage: res.data?.triage,
        clinics: res.data?.nearby_clinics,
      };

      setMessages((prev) => [...prev, aiMessage]);

      // 🚨 [修改] 這裡把原本強迫清空 session 的邏輯移除了！
      // 讓後端的 session_store 去決定什麼時候真的結束連線

    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: "系統暫時無法連線，請稍後再試。",
          type: "invalid",
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const dismissEmergency = () => {
    setIsEmergency(false);
    setSessionId(undefined);
    setMessages([
      {
        role: "ai",
        content: "您好，我是 AI 醫療問診助理。請描述您目前的身體症狀，我來協助您找到合適的科別。",
      },
    ]);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50 font-sans">

      {/* ── 緊急警告遮罩 ── */}
      {isEmergency && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-red-500/30 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl p-8 max-w-sm w-full mx-4 text-center space-y-5 border border-red-100">
            <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800">偵測到緊急症狀</h2>
              <p className="text-sm text-slate-500 mt-1 leading-relaxed">
                您描述的症狀可能需要立即就醫，請撥打 119 或前往最近的急診室。
              </p>
            </div>
            <a
              href="tel:119"
              className="block w-full bg-red-500 hover:bg-red-600 text-white font-semibold py-3 rounded-xl transition-colors text-sm"
            >
              立即撥打 119
            </a>
            <button
              onClick={dismissEmergency}
              className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
            >
              返回問診
            </button>
          </div>
        </div>
      )}

      {/* ── Header ── */}
      <header className="bg-white border-b border-slate-100 px-4 py-3 flex items-center gap-3 shrink-0">
        <div className="w-8 h-8 bg-sky-50 rounded-full flex items-center justify-center">
          <svg className="w-4 h-4 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </div>
        <div>
          <h1 className="text-sm font-semibold text-slate-800">AI 醫療問診助理</h1>
          <p className="text-xs text-slate-400">症狀評估・科別推薦・診所查詢</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
          <span className="text-xs text-slate-400">服務中</span>
        </div>
      </header>

      {/* ── 聊天區 ── */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} msg={msg} />
        ))}

        {/* 載入中動畫 */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── 免責聲明 ── */}
      <p className="text-center text-xs text-slate-300 pb-1 px-4 shrink-0">
        本服務僅供參考，不構成醫療診斷。如有緊急狀況請撥打 119。
      </p>

      {/* ── 輸入區 ── */}
      <div className="bg-white border-t border-slate-100 px-4 py-3 shrink-0">
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-2xl px-4 py-2 focus-within:border-sky-300 focus-within:bg-white transition-all duration-200">
          <input
            ref={inputRef}
            className="flex-1 bg-transparent text-sm text-slate-700 placeholder-slate-400 outline-none"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="描述您的症狀，例如：頭痛兩天了..."
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="shrink-0 w-8 h-8 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-200 text-white rounded-full flex items-center justify-center transition-colors duration-200"
          >
            <svg className="w-4 h-4 translate-x-px" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.269 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}