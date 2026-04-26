import time
from typing import Optional
from .manager import DatabaseManager


def init_database(db_manager: DatabaseManager) -> bool:
    """Проверка и инициализация базы данных при старте"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            print(f"🔄 Проверка БД (попытка {attempt + 1}/{max_attempts})...")
            
            conn = db_manager.get_connection()
            
            check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'companies'
            );
            """
            
            with conn.cursor() as cur:
                cur.execute(check_query)
                companies_exists = cur.fetchone()[0]
                
                if not companies_exists:
                    print("📋 Таблицы не найдены, создаем...")
                    
                    create_tables = """
                    CREATE TABLE IF NOT EXISTS companies (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS employees (
                        id SERIAL PRIMARY KEY,
                        last_name VARCHAR(100) NOT NULL,
                        first_name VARCHAR(100) NOT NULL,
                        middle_name VARCHAR(100),
                        company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE INDEX IF NOT EXISTS idx_employees_company_id ON employees(company_id);
                    CREATE INDEX IF NOT EXISTS idx_employees_names ON employees(last_name, first_name);
                    """
                    
                    cur.execute(create_tables)
                    conn.commit()
                    
                    test_data = """
                    INSERT INTO companies (name) VALUES 
                        ('Google'), 
                        ('Yandex'), 
                        ('Mail.ru')
                    ON CONFLICT (name) DO NOTHING;
                    
                    INSERT INTO employees (last_name, first_name, middle_name, company_id) 
                    SELECT 'Иванов', 'Иван', 'Иванович', id FROM companies WHERE name = 'Google'
                    UNION ALL
                    SELECT 'Петров', 'Петр', 'Петрович', id FROM companies WHERE name = 'Yandex'
                    UNION ALL
                    SELECT 'Сидорова', 'Анна', 'Сергеевна', id FROM companies WHERE name = 'Mail.ru';
                    """
                    
                    cur.execute(test_data)
                    conn.commit()
                    
                    print("✅ База данных инициализирована с тестовыми данными")
                else:
                    print("✅ База данных уже существует")
                    cur.execute("SELECT COUNT(*) FROM companies;")
                    companies_count = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM employees;")
                    employees_count = cur.fetchone()[0]
                    print(f"📊 Компаний: {companies_count}, Сотрудников: {employees_count}")
                
            return True
            
        except Exception as e:
            print(f"⚠️ Ошибка инициализации БД: {e}")
            if attempt < max_attempts - 1:
                time.sleep(3)
            else:
                print("❌ Не удалось инициализировать базу данных")
                return False
    
    return False


async def reset_database(db_manager: DatabaseManager) -> dict:
    """Сброс и переинициализация базы данных"""
    try:
        conn = db_manager.get_connection()
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS employees CASCADE;")
            cur.execute("DROP TABLE IF EXISTS companies CASCADE;")
            conn.commit()
        
        if init_database(db_manager):
            return {"status": "success", "message": "База данных сброшена и инициализирована заново"}
        else:
            return {"status": "error", "message": "Ошибка при переинициализации"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
