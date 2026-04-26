from .config import DATABASE_URL, FRONTEND_DIR, MOCK_MODE, GIGACHAT_API_KEY
from .database.manager import DatabaseManager
from .database.init import init_database, reset_database
from .llm.factory import get_giga_llm
from .agent.sql_agent import SQLAgent
from .websocket.manager import ConnectionManager, websocket_endpoint
from .tools.sql_tools import set_db_manager

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(title="SQL Assistant with GigaChat")

db_manager = DatabaseManager(DATABASE_URL)
set_db_manager(db_manager)

giga_llm = get_giga_llm()  # ← здесь используется GIGACHAT_API_KEY из config
agent = SQLAgent(llm=giga_llm)
manager = ConnectionManager()


@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket_endpoint(websocket, agent, manager)


@app.post("/api/reset-database")
async def reset_db_endpoint():
    return await reset_database(db_manager)


@app.get("/api/schema")
async def get_schema_api():
    return db_manager.get_table_schema()


@app.get("/api/health")
async def health_check():
    try:
        db_manager.get_connection()
        return {
            "status": "healthy",
            "database": "connected",
            "gigachat": "connected" if giga_llm else "not configured",
            "mock_mode": MOCK_MODE,
            "key_present": bool(GIGACHAT_API_KEY)  # 🔍 Для отладки
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


frontend_path = Path(FRONTEND_DIR)
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def root():
    index = frontend_path / "index.html"
    if index.exists():
        from fastapi.responses import HTMLResponse
        with open(index, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {"message": "SQL Assistant API", "docs": "/docs"}


@app.on_event("startup")
async def startup():
    print("🚀 Запуск...")
    print(f"🔑 API ключ: {'✅ есть' if GIGACHAT_API_KEY else '❌ нет'}")
    init_database(db_manager)
    print(f"🌐 http://0.0.0.0:8000")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)