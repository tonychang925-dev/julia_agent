"""WebSocket transport shell for F4 analyst chat."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date

from runtime.capability.financial.interface.analyst_chat.session import AnalystSession

try:
    from fastapi import APIRouter, WebSocket
except Exception:  # pragma: no cover
    class APIRouter:  # type: ignore[no-redef]
        def websocket(self, path: str):
            def decorator(func):
                return func
            return decorator

    class WebSocket:  # type: ignore[no-redef]
        async def accept(self) -> None: ...
        async def receive_text(self) -> str: ...
        async def send_text(self, data: str) -> None: ...


router = APIRouter()


@router.websocket("/analyst/chat")
async def analyst_chat(ws: WebSocket) -> None:
    await ws.accept()
    session = AnalystSession(trade_date=date.today())
    try:
        while True:
            message = await ws.receive_text()
            response = session.handle_text(message)
            await ws.send_text(json.dumps(asdict(response), ensure_ascii=False, default=str))
    finally:
        session.close()
