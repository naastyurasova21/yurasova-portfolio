CREATE TYPE contact_group_enum AS ENUM (
    'Общие',
    'Друзья',
    'Работа',
    'Семья',
    'Сервис',
    'Соседи',
    'Другое'
);

CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    phone_number VARCHAR(16) NOT NULL UNIQUE CHECK (phone_number ~ '^\+[1-9][0-9]{1,14}$'), -- just E.164 re check
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_favorite BOOLEAN DEFAULT FALSE,
    contact_group contact_group_enum NOT NULL DEFAULT 'Общие'
);

CREATE INDEX idx_contacts_last_name ON contacts(last_name);
CREATE INDEX idx_contacts_phone ON contacts(phone_number);
CREATE INDEX idx_contacts_group ON contacts(contact_group);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

INSERT INTO contacts (last_name, first_name, middle_name, phone_number, note, contact_group) VALUES
    ('Иванов', 'Евгений', 'Аркадьевич', '+79998764555', 'Одногруппник', 'Друзья'),
    ('Ефимов', 'Арсений', 'Максимович', '+79994391166', 'Одноклассник', 'Друзья'),
    ('Комарова', 'Елена', 'Александровна', '+78756746577', 'Коллега', 'Работа'),
    ('Алимов', 'Дмитрий', 'Миронович', '+79994567890', 'Сосед', 'Соседи'),
    ('Игонина', 'Анастасия', 'Евгеньевна', '+79991670901', 'Мастер маникюра', 'Сервис'),
    ('Lake', 'Jane', NULL, '+12025657147', 'Контакт из США', 'Работа'),
    ('Dubois', 'Claire', NULL, '+33142278186', 'Незнакомка из Франции', 'Другое'),
    ('Silva', 'Mateus', NULL, '+5511912345678', 'По работе из Бразилии', 'Работа'),
    ('Bjornosiva', 'Mila', NULL, '+3545885522', 'Классно печёт торты', 'Сервис');
