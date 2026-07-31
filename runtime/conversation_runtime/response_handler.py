from __future__ import annotations

from dataclasses import dataclass

from .bridge.cognitive_bridge import CognitiveBridge, CognitiveResponse
from .turn_manager import ConversationTurn


@dataclass
class ResponseHandler:
    bridge: CognitiveBridge

    def generate_response(self, turn: ConversationTurn) -> CognitiveResponse:
        self.bridge.send_message(turn.user.text, session_id=turn.session_id, turn_id=turn.turn_id)
        return self.bridge.receive_response(session_id=turn.session_id, turn_id=turn.turn_id)
