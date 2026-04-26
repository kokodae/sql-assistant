import re
import json
from typing import List, Dict

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from ..config import MOCK_MODE
from ..tools.sql_tools import execute_sql, get_schema

SYSTEM_PROMPT = """Ты - SQL ассистент, работающий с базой данных PostgreSQL.

База данных содержит таблицы:
1. companies (id, name, created_at) - компании
2. employees (id, last_name, first_name, middle_name, company_id, created_at) - работники

При запросах на создание/изменение данных:
1. Генерируй SQL запрос в блоке ```sql ... ```
2. Объясняй что делаешь на русском
3. Подтверждай успешное выполнение

Пример ответа на "создай сотрудника Иванова Ивана Ивановича":
```sql
INSERT INTO employees (last_name, first_name, middle_name, company_id) 
VALUES ('Иванов', 'Иван', 'Иванович', 1);```

Твои возможности:
- Генерировать и выполнять SQL запросы на основе запросов пользователя
- Показывать результаты запросов в понятном формате
- Изменять структуру таблиц (добавлять/удалять/изменять колонки)
- Создавать и удалять таблицы

Правила работы:
1. ВСЕГДА используй инструмент get_schema перед изменением структуры БД
2. Для SELECT запросов показывай результаты в виде таблицы или списка
3. При изменении данных всегда подтверждай операцию
4. Проверяй безопасность SQL запросов (избегай DROP DATABASE)
5. Объясняй пользователю что ты делаешь на каждом шаге
6. При выборке ВСЕГДА используй `SELECT DISTINCT`, чтобы исключить дубликаты.
7. Если запрос на выборку возвращает пустой результат (0 строк), отвечай строго: "Информация отсутствует."

Формат ответа:
1. Краткое объяснение на русском языке
2. НИКОГДА не показывай пользователю сырой JSON или SQL-код.
3. Если запрос на получение данных, отвечай сразу оформленным списком или таблицей.
4. Пиши кратко. Например: "Вот список компаний:\n- Google\n- Yandex\n..."
5. Технические детали (успех выполнения, количество строк) скрывай, если пользователь не спрашивал специально.
6. Дополнительные комментарии при необходимости

Если запрос пользователя не связан с базой данных, вежливо напомни о твоем назначении.
"""


class SQLAgent:
    def __init__(self, llm):
        self.llm = llm
        self.tools = {t.name: t for t in [execute_sql, get_schema]}
    
    def _mock_response(self, message: str) -> str:
        return f"🔧 MOCK: {message}"
    
    async def process_message(self, message: str, chat_history: List[Dict] = None) -> Dict:
        if chat_history is None:
            chat_history = []
        if MOCK_MODE or not self.llm:
            return {"type": "response", "content": self._mock_response(message), "tools_used": ["mock"]}
        
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        for msg in chat_history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=message))
        
        try:
            response = self.llm.invoke(messages)
            text = response.content if hasattr(response, 'content') else str(response)
            
            # Извлекаем SQL-блоки сразу
            sql_blocks = re.findall(r'```sql\s*(.+?)\s*```', text, re.DOTALL)
            
            if sql_blocks:
                last_query = sql_blocks[-1].strip()
                try:
                    raw_res = execute_sql.invoke(last_query)
                    res_data = json.loads(raw_res)
                    
                    if not res_data.get("success"):
                        text = f"❌ {res_data.get('error', 'Ошибка БД')}"
                        
                    elif res_data.get("type") == "select":
                        rows = res_data.get("data", [])
                        
                        seen = set()
                        unique_rows = []
                        for row in rows:
                            key = tuple(sorted(row.items()))
                            if key not in seen:
                                seen.add(key)
                                unique_rows.append(row)
                        
                        if not unique_rows:
                            text = "Информация отсутствует."
                        elif 'name' in unique_rows[0]:
                            text = "\n".join(f"- {r['name']}" for r in unique_rows if r.get('name'))
                        elif 'last_name' in unique_rows[0]:
                            text = "\n".join(
                                f"- {r['last_name']} {r['first_name']} {r.get('middle_name', '')}".strip() 
                                for r in unique_rows
                            )
                        else:
                            first_key = next(iter(unique_rows[0]))
                            text = "\n".join(f"- {r.get(first_key, '')}" for r in unique_rows)
                            
                    else:  # INSERT / UPDATE / DELETE
                        row_count = res_data.get("row_count", 0)
                        text = f"✅ Затронуто строк: {row_count}" if row_count else "⚠️ Записи не найдены или не изменены."
                        
                except Exception as e:
                    text = f"❌ Ошибка: {str(e)}"
            else:
                # Если SQL не было, убираем только визуальный мусор из ответа модели
                text = re.sub(r'🔧\s*sql|📊\s*Результат:?', '', text).strip()
            
            return {"type": "response", "content": text, "tools_used": ["sql"] if sql_blocks else []}
            
        except Exception as e:
            return {"type": "error", "content": f"❌ {str(e)}"}
