import os
from dotenv import load_dotenv
import threading
from typing import Set
import logging
from aiogram.types import InlineQuery

load_dotenv()

"""
Иерархия доступа:
1. SUPER_ADMIN - полный доступ
2. ADMIN_IDS - доступ к админ-панели + инлайн
3. USER_IDS - только инлайн-режим
"""

class AccessControl:
    _lock = threading.Lock()
    _admin_ids: Set[int] = set()
    _user_ids: Set[int] = set()
    _super_admin_id: int = int(os.getenv("SUPER_ADMIN", 0))

    @classmethod
    def load_ids(cls):
        """Загружает ID из переменных окружения"""
        with cls._lock:
            admin_ids = os.getenv("ADMIN_IDS", "")
            user_ids = os.getenv("USER_IDS", "")
            
            cls._admin_ids = {int(id_str.strip()) for id_str in admin_ids.split(",") if id_str.strip()}
            cls._user_ids = {int(id_str.strip()) for id_str in user_ids.split(",") if id_str.strip()}

    @classmethod
    def is_super_admin(cls, user_id: int) -> bool:
        """Проверяет, является ли пользователь супер-админом"""
        return user_id == cls._super_admin_id

    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        with cls._lock:
            if not cls._admin_ids:
                cls.load_ids()
            return user_id in cls._admin_ids or user_id == cls._super_admin_id
            
    @classmethod
    def is_user(cls, user_id: int) -> bool:
        if not hasattr(cls, '_cached_users'):
            with cls._lock:
                cls.load_ids()
                cls._cached_users = cls._user_ids.union(cls._admin_ids)
                if cls._super_admin_id:
                    cls._cached_users.add(cls._super_admin_id)
        return user_id in cls._cached_users

    @classmethod
    def is_user(cls, user_id: int) -> bool:
        """Проверяет, есть ли у пользователя доступ"""
        return cls.is_admin(user_id) or user_id in cls.get_user_ids()

    @classmethod
    def add_user(cls, user_id: int):
        """Добавляет пользователя и обновляет .env"""
        with cls._lock:
            if not cls._user_ids:
                cls.load_ids()
                
            if user_id not in cls._user_ids:
                cls._user_ids.add(user_id)
                cls._update_env()

    @classmethod
    def add_admin(cls, user_id: int):
        """Добавляет администратора и обновляет .env"""
        with cls._lock:
            if not cls._admin_ids:
                cls.load_ids()
                
            if user_id not in cls._admin_ids:
                cls._admin_ids.add(user_id)
                cls._update_env()

    @classmethod
    def remove_admin(cls, user_id: int):
        """Удаляет администратора (кроме SUPER_ADMIN)"""
        with cls._lock:
            if user_id == cls._super_admin_id:
                return False
                
            if user_id in cls._admin_ids:
                cls._admin_ids.remove(user_id)
                cls._update_env()
                return True
            return False

    @classmethod
    def get_admin_ids(cls) -> Set[int]:
        """Возвращает множество ID администраторов"""
        with cls._lock:
            if not cls._admin_ids:
                cls.load_ids()
            return cls._admin_ids.copy()

    @classmethod
    def get_user_ids(cls) -> Set[int]:
        """Возвращает множество ID пользователей"""
        with cls._lock:
            if not cls._user_ids:
                cls.load_ids()
            return cls._user_ids.copy()

    @classmethod
    def _update_env(cls):
        """Обновляет .env файл"""
        env_vars = {
            "BOT_TOKEN": os.getenv("BOT_TOKEN"),
            "SUPER_ADMIN": str(cls._super_admin_id),
            "ADMIN_IDS": ",".join(map(str, cls._admin_ids)),
            "USER_IDS": ",".join(map(str, cls._user_ids)),
            "LOG_CHANNEL_ID": os.getenv("LOG_CHANNEL_ID", "")
        }
        
        with open(".env", "w") as f:
            for key, value in env_vars.items():
                if value:
                    f.write(f"{key}={value}\n")
      
    @classmethod
    def remove_user(cls, user_id: int) -> bool:
        """Удаляет пользователя и обновляет .env"""
        with cls._lock:
            if user_id in cls._user_ids:
                cls._user_ids.remove(user_id)
                cls._update_env()
                return True
            return False
    
# Инициализация при импорте
AccessControl.load_ids()
