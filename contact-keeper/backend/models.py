from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, List
from datetime import datetime
import re
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

ALL_GROUPS_LABEL = 'Все'
class ContactGroup(StrEnum):
    GENERAL = 'Общие'
    FRIENDS = 'Друзья'
    WORK = 'Работа'
    FAMILY = 'Семья'
    SERVICE = 'Сервис'
    NEIGHBORS = 'Соседи'
    OTHER = 'Другое'

    @classmethod
    def parse(cls, value: Optional[str]) -> 'ContactGroup':
        raw_value = (value or cls.GENERAL.value).strip()
        try:
            return cls(raw_value)
        except ValueError as error:
            raise ValueError('Выберите группу из списка.') from error

    @classmethod
    def values(cls) -> List[str]:
        return [group.value for group in cls]

DEFAULT_CONTACT_GROUP = ContactGroup.GENERAL.value
CONTACT_GROUPS = ContactGroup.values()

@dataclass
class Contact:
    id: Optional[int]
    last_name: str
    first_name: str
    middle_name: Optional[str]
    phone_number: str
    note: Optional[str]
    contact_group: ContactGroup
    is_favorite: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)

    @property
    def formatted_phone(self) -> str:
        try:
            parsed_number = phonenumbers.parse(self.phone_number, None)
        except NumberParseException:
            return self.phone_number

        if phonenumbers.is_valid_number(parsed_number):
            return phonenumbers.format_number(parsed_number, PhoneNumberFormat.INTERNATIONAL)

        return self.phone_number

    @staticmethod
    def normalize_phone_number(phone_number: str) -> str:
        raw_phone = (phone_number or '').strip()
        if not raw_phone:
            raise ValueError('Укажите номер телефона.')

        if not raw_phone.startswith('+'):
            digits_only = re.sub(r'\D', '', raw_phone)
            raw_phone = f'+{digits_only}'

        try:
            parsed_number = phonenumbers.parse(raw_phone, None)
        except NumberParseException as error:
            raise ValueError('Введите корректный номер телефона с кодом страны.') from error

        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError('Введите корректный номер телефона с кодом страны.')

        return phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id'),
            last_name=data['last_name'],
            first_name=data['first_name'],
            middle_name=data.get('middle_name'),
            phone_number=data['phone_number'],
            note=data.get('note'),
            contact_group=ContactGroup.parse(data.get('contact_group', DEFAULT_CONTACT_GROUP)),
            is_favorite=data.get('is_favorite', False),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

class ContactRepository:
    def __init__(self, db):
        self.db = db

    def get_all(self, group: Optional[str] = None, search: Optional[str] = None) -> List[Contact]:
        query = "SELECT * FROM contacts WHERE 1=1"
        params = []

        if group and group != ALL_GROUPS_LABEL:
            query += " AND contact_group = %s"
            params.append(group)

        if search:
            search_pattern = f'%{search}%'
            phone_search = re.sub(r'\D', '', search)
            phone_pattern = f'%{phone_search}%' if phone_search else search_pattern
            query += """ AND (
                last_name ILIKE %s OR 
                first_name ILIKE %s OR 
                regexp_replace(phone_number, '\\D', '', 'g') ILIKE %s OR 
                note ILIKE %s
            )"""
            params.extend([search_pattern, search_pattern, phone_pattern, search_pattern])

        query += " ORDER BY is_favorite DESC, last_name, first_name"

        results = self.db.execute_query(query, params, fetch_all=True)
        return [Contact.from_dict(row) for row in results]

    def get_by_id(self, contact_id: int) -> Optional[Contact]:
        query = "SELECT * FROM contacts WHERE id = %s"
        result = self.db.execute_query(query, (contact_id,), fetch_one=True)
        return Contact.from_dict(result) if result else None

    def create(self, contact: Contact) -> int:
        query = """
            INSERT INTO contacts
            (last_name, first_name, middle_name, phone_number, note, contact_group, is_favorite)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            contact.last_name, contact.first_name, contact.middle_name,
            contact.phone_number, contact.note, contact.contact_group.value,
            contact.is_favorite
        )
        result = self.db.execute_query(query, params, fetch_one=True)
        return result['id']

    def update(self, contact_id: int, contact: Contact) -> bool:
        query = """
            UPDATE contacts SET
                last_name = %s, first_name = %s, middle_name = %s,
                phone_number = %s, note = %s, contact_group = %s,
                is_favorite = %s
            WHERE id = %s
        """
        params = (
            contact.last_name, contact.first_name, contact.middle_name,
            contact.phone_number, contact.note, contact.contact_group.value,
            contact.is_favorite, contact_id
        )
        self.db.execute_query(query, params)
        return True

    def delete(self, contact_id: int) -> bool:
        query = "DELETE FROM contacts WHERE id = %s"
        self.db.execute_query(query, (contact_id,))
        return True

    def get_groups(self) -> List[str]:
        return [ALL_GROUPS_LABEL] + CONTACT_GROUPS

    def toggle_favorite(self, contact_id: int) -> bool:
        query = "UPDATE contacts SET is_favorite = NOT is_favorite WHERE id = %s"
        updated_rows = self.db.execute_query(query, (contact_id,), return_rowcount=True)
        return updated_rows > 0
