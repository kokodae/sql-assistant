import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/company_db")
GIGACHAT_API_KEY = os.getenv("GIGACHAT_CREDENTIALS", os.getenv("GIGACHAT_API_KEY", ""))
GIGACHAT_AUTH_URL = os.getenv("GIGACHAT_AUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
GIGACHAT_API_URL = os.getenv("GIGACHAT_API_URL", "https://gigachat.devices.sberbank.ru/api/v1")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
FRONTEND_DIR = os.getenv("FRONTEND_DIR", "../frontend")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

print(f"🔧 MOCK_MODE: {MOCK_MODE}")
print(f"🔑 GIGACHAT_API_KEY: {'Set' if GIGACHAT_API_KEY else 'Not set'}")