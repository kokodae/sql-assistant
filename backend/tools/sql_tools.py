import json
from langchain_core.tools import tool

_db_manager = None


def set_db_manager(manager):
    global _db_manager
    _db_manager = manager


@tool
def execute_sql(query: str) -> str:
    """Выполняет SQL запрос к базе данных PostgreSQL."""
    if _db_manager is None:
        return json.dumps({"success": False, "error": "DB not initialized"}, ensure_ascii=False)
    result = _db_manager.execute_query(query)
    return json.dumps(result, default=str, ensure_ascii=False, indent=2)


@tool
def get_schema(dummy: str = "") -> str:
    """Получает текущую схему базы данных."""
    if _db_manager is None:
        return json.dumps({"error": "DB not initialized"}, ensure_ascii=False)
    schema = _db_manager.get_table_schema()
    return json.dumps(schema, default=str, ensure_ascii=False, indent=2)
