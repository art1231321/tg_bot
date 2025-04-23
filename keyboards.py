from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура основного меню для админов"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Список голосовых")],
            [KeyboardButton(text="✏️ Переименовать"), KeyboardButton(text="❌ Удалить")],
            [KeyboardButton(text="🔄 Обновить меню")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура админ-панели"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👑 Управление админами")],
            [KeyboardButton(text="🗣 Управление говорунами")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )

def get_admin_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления администраторами"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Список админов")],
            [KeyboardButton(text="➕ Добавить админа")],
            [KeyboardButton(text="➖ Удалить админа")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def get_speaker_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления говорунами"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Список говорунов")],
            [KeyboardButton(text="➕ Добавить говоруна")],
            [KeyboardButton(text="➖ Удалить говоруна")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def get_voices_keyboard(action: str) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора голосовых сообщений"""
    from voice_storage import VoiceStorage  # Импортируем здесь, чтобы избежать циклических импортов
    
    storage = VoiceStorage()
    builder = InlineKeyboardBuilder()
    for title in storage.voices:
        builder.button(text=title, callback_data=f"{action}:{title}")
    builder.adjust(1)
    return builder.as_markup()

def get_access_request_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для обработки запросов доступа"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"approve:{user_id}")
    builder.button(text="❌ Отклонить", callback_data=f"reject:{user_id}")
    return builder.as_markup()
