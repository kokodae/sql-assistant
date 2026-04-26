import asyncio
from typing import List, Dict

from fastapi import WebSocket, WebSocketDisconnect

from ..agent.sql_agent import SQLAgent


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.chat_histories: Dict[WebSocket, List] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.chat_histories[websocket] = []

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.chat_histories:
            del self.chat_histories[websocket]

    async def send_message(self, message: Dict, websocket: WebSocket):
        await websocket.send_json(message)


async def websocket_endpoint(websocket: WebSocket, agent: SQLAgent, manager: ConnectionManager):
    """WebSocket для чата"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()
            
            if not user_message:
                continue
            
            await manager.send_message({
                "type": "status",
                "content": "Обработка запроса..."
            }, websocket)
            
            chat_history = manager.chat_histories.get(websocket, [])
            response = await agent.process_message(user_message, chat_history)
            
            # Сохранение истории
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": response.get("content", "")})
            if len(chat_history) > 20:
                chat_history = chat_history[-20:]
                manager.chat_histories[websocket] = chat_history
            
            await manager.send_message({
                "type": "response",
                "content": response.get("content", ""),
                "tools_used": response.get("tools_used", [])
            }, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await manager.send_message({
                "type": "error",
                "content": f"❌ Ошибка: {str(e)}"
            }, websocket)
        except:
            pass
