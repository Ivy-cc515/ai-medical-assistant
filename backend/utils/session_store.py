from schemas.conversation_state import ConversationState


# In-memory session store（生產環境可替換為 Redis）
_sessions: dict[str, ConversationState] = {}


def get_or_create(session_id: str) -> ConversationState:
    if session_id not in _sessions:
        _sessions[session_id] = ConversationState()
    return _sessions[session_id]


def save(session_id: str, state: ConversationState) -> None:
    _sessions[session_id] = state


def clear(session_id: str) -> None:
    _sessions.pop(session_id, None)