import time
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Optional


class DatabaseManager:
    """Менеджер для работы с PostgreSQL"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.connection = None
        self.max_retries = 5
        self.retry_delay = 3
        
    def get_connection(self):
        """Получение соединения с БД"""
        for attempt in range(self.max_retries):
            try:
                if not self.connection or self.connection.closed:
                    print(f"🔄 Подключение к БД ({attempt + 1}/{self.max_retries})...")
                    self.connection = psycopg2.connect(
                        self.db_url,
                        connect_timeout=10
                    )
                    print("✅ Подключение к БД установлено")
                return self.connection
            except Exception as e:
                print(f"⚠️ Ошибка подключения: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
    
    def execute_query(self, query: str, params: tuple = None) -> Dict:
        """Выполнение SQL запроса"""
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                
                query_upper = query.strip().upper()
                if query_upper.startswith(('SELECT', 'SHOW', 'WITH', 'EXPLAIN')):
                    results = cur.fetchall()
                    return {
                        "success": True,
                        "type": "select",
                        "data": results,
                        "row_count": len(results)
                    }
                else:
                    conn.commit()
                    return {
                        "success": True,
                        "type": "modify",
                        "row_count": cur.rowcount,
                        "message": f"Запрос выполнен успешно. Затронуто строк: {cur.rowcount}"
                    }
        except Exception as e:
            try:
                conn.rollback()
            except:
                pass
            return {
                "success": False,
                "type": "error",
                "error": str(e)
            }
    
    def get_table_schema(self) -> Dict:
        query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        result = self.execute_query(query)
        if result["success"]:
            schema = {}
            for row in result["data"]:
                table = row["table_name"]
                if table not in schema:
                    schema[table] = []
                schema[table].append({
                    "column": row["column_name"],
                    "type": row["data_type"]
                })
            return schema
        return {}