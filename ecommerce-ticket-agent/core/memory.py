from typing import Dict, List


class ConversationMemory:
    """Per-ticket conversation memory for multi-turn dialogue."""

    def __init__(self, max_turns: int = 10):
        self._store: Dict[int, List[dict]] = {}
        self._max_turns = max_turns

    def add(self, ticket_id: int, role: str, content: str):
        if ticket_id not in self._store:
            self._store[ticket_id] = []
        self._store[ticket_id].append({"role": role, "content": content})
        if len(self._store[ticket_id]) > self._max_turns * 2:
            self._store[ticket_id] = self._store[ticket_id][-(self._max_turns * 2):]

    def get_history(self, ticket_id: int) -> List[dict]:
        return self._store.get(ticket_id, [])

    def get_formatted(self, ticket_id: int) -> str:
        history = self.get_history(ticket_id)
        if not history:
            return "(无历史对话)"
        lines = []
        for msg in history:
            role_label = "客户" if msg["role"] == "customer" else "客服" if msg["role"] == "agent" else "系统"
            lines.append(f"{role_label}: {msg['content']}")
        return "\n".join(lines)

    def clear(self, ticket_id: int):
        self._store.pop(ticket_id, None)


memory = ConversationMemory()
