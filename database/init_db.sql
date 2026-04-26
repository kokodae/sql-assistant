-- Подключаемся к существующей базе данных
\c company_db;

-- Удаляем старые таблицы если нужно (опционально, для чистой установки)
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS companies CASCADE;

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

COMMENT ON TABLE companies IS 'Таблица компаний';
COMMENT ON TABLE employees IS 'Таблица работников';
COMMENT ON COLUMN employees.company_id IS 'Внешний ключ к таблице компаний';

-- Добавление тестовых данных
INSERT INTO companies (name) VALUES 
    ('Google'), 
    ('Yandex'), 
    ('Mail.ru')
ON CONFLICT (name) DO NOTHING;

DO $$
DECLARE
    google_id INTEGER;
    yandex_id INTEGER;
    mail_id INTEGER;
BEGIN
    SELECT id INTO google_id FROM companies WHERE name = 'Google';
    SELECT id INTO yandex_id FROM companies WHERE name = 'Yandex';
    SELECT id INTO mail_id FROM companies WHERE name = 'Mail.ru';
    
    -- Добавляем сотрудников
    INSERT INTO employees (last_name, first_name, middle_name, company_id) VALUES
        ('Иванов', 'Иван', 'Иванович', google_id),
        ('Петров', 'Петр', 'Петрович', google_id),
        ('Сидорова', 'Анна', 'Сергеевна', yandex_id),
        ('Козлов', 'Дмитрий', 'Александрович', mail_id)
    ON CONFLICT DO NOTHING;
END $$;

SELECT 'Tables created successfully!' as status;
\dt
