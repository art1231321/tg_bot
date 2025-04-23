import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineQuery,
    InlineQueryResultVoice,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Мои импорты
from video_processor import convert_video_to_voice
from access_control import AccessControl
from keyboards import (
    get_main_keyboard,
    get_admin_main_keyboard,
    get_admin_management_keyboard,
    get_speaker_management_keyboard,
    get_voices_keyboard,
    get_access_request_keyboard
)
from states import RenameStates, AccessStates, AdminStates
from voice_storage import VoiceStorage

# Загрузка конфигурации
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
SUPER_ADMIN = int(os.getenv("SUPER_ADMIN"))
storage = VoiceStorage()  # Инициализация хранилища голосовых

# Состояния FSM
def get_admins():
    """Динамически читает ADMIN_IDS из файла"""
    load_dotenv()  # Перезагружаем .env
    return [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

def get_users():
    """Динамически читает USER_IDS из файла"""
    load_dotenv()  # Перезагружаем .env
    return [int(id) for id in os.getenv("USER_IDS", "").split(",") if id]
    
class AdminStates(StatesGroup):
    waiting_admin_id = State()
    waiting_speaker_id = State()
    
def update_env_file(key: str, value: str):
    """Обновляет значение в .env файле"""
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    with open('.env', 'w') as f:
        for line in lines:
            if line.startswith(key):
                f.write(f"{key}={value}\n")
            else:
                f.write(line)

# ==============================================
# Основные обработчики команд
# ==============================================
@dp.message(Command("admin_panel"))
async def admin_panel(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        await message.answer("🚫 Только для SUPER_ADMIN!")
        return
    
    await message.answer(
        "Панель управления SUPER_ADMIN:",
        reply_markup=get_admin_main_keyboard()
    )

@dp.message(CommandStart())
async def cmd_start(message: Message):
    if AccessControl.is_admin(message.from_user.id):
        await message.answer(
            "🎙️ Админ-панель бота для голосовых сообщений",
            reply_markup=get_main_keyboard()
        )
    elif AccessControl.is_user(message.from_user.id):
        await message.answer(
            "🎙️ Бот для голосовых сообщений\n\n"
            "Вы можете использовать инлайн-режим (@ваш_бот) для отправки сохранённых сообщений"
        )
    else:
        await message.answer(
            "🚫 Этот бот доступен только для авторизованных пользователей",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="📨 Запросить доступ", callback_data="request_access")
            ]])
        )
               
# ======================
# Вспомогательные функции
# ======================

async def get_user_info(user_id: int) -> str:
    try:
        user = await bot.get_chat(user_id)
        return f"@{user.username}" if user.username else f"{user.full_name} (ID: {user.id})"
    except Exception:
        return str(user_id)

async def get_user_display_info(user_id: int) -> str:
    """Возвращает строку с информацией о пользователе (username + ID)"""
    try:
        user = await bot.get_chat(user_id)
        if user.username:
            return f"@{user.username} (ID: {user_id})"
        return f"{user.full_name} (ID: {user_id})"
    except Exception:
        return f"ID: {user_id}"

def reload_env_vars():
    """Принудительно перезагружает переменные окружения"""
    global SUPER_ADMIN
    load_dotenv(override=True)
    SUPER_ADMIN = int(os.getenv("SUPER_ADMIN"))

# ==============================================
# Обработчики для управления голосовыми
# ==============================================

@dp.message(F.text == "📋 Список голосовых")
async def list_voices(message: Message):
    if not AccessControl.is_admin(message.from_user.id):
        return
    
    if not storage.voices:
        await message.answer("Нет сохранённых сообщений", reply_markup=get_main_keyboard())
        return
    
    voices_list = "\n".join(f"🔹 {title}" for title in storage.voices)
    await message.answer(
        f"📋 Сохранённые сообщения ({len(storage.voices)}):\n\n{voices_list}",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "✏️ Переименовать")
async def rename_voice_start(message: Message):
    if not AccessControl.is_admin(message.from_user.id):
        return
    
    if not storage.voices:
        await message.answer("Нет сообщений для переименования", reply_markup=get_main_keyboard())
        return
    
    await message.answer(
        "Выберите сообщение для переименования:",
        reply_markup=get_voices_keyboard("rename")
    )

@dp.message(F.text == "❌ Удалить")
async def delete_voice_start(message: Message):
    if not AccessControl.is_admin(message.from_user.id):
        return
    
    if not storage.voices:
        await message.answer("Нет сообщений для удаления", reply_markup=get_main_keyboard())
        return
    
    await message.answer(
        "Выберите сообщение для удаления:",
        reply_markup=get_voices_keyboard("delete")
    )

@dp.message(F.text == "🔄 Обновить меню")
async def refresh_menu(message: Message):
    if not AccessControl.is_admin(message.from_user.id):
        return
    
    await message.answer("Меню обновлено:", reply_markup=get_main_keyboard())

# ==============================================
# Обработчики медиа
# ==============================================

@dp.message(F.voice)
async def handle_voice(message: Message):
    if not AccessControl.is_admin(message.from_user.id):
        return
    
    title = f"Голосовое {len(storage.voices) + 1}"
    if storage.save_voice(title, message.voice.file_id):
        await message.reply(f"✅ Сохранено как: {title}", reply_markup=get_main_keyboard())
    else:
        await message.reply("⚠️ Это сообщение уже было сохранено ранее", reply_markup=get_main_keyboard())

@dp.message(F.video | F.video_note)
async def handle_video(message: Message):
    if not AccessControl.is_admin(message.from_user.id):
        return
    
    try:
        await message.reply("🔄 Конвертирую видео в голосовое...")
        if file_id := await convert_video_to_voice(message):
            title = f"Видео-аудио {len(storage.voices) + 1}"
            if storage.save_voice(title, file_id):
                await message.reply(f"✅ Сохранено как: {title}")
            else:
                await message.reply("⚠️ Это сообщение уже было сохранено ранее")
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        await message.reply("⚠️ Ошибка при обработке видео")

# ==============================================
# Обработчики callback
# ==============================================

@dp.callback_query(F.data.startswith("rename:"))
async def rename_voice_callback(callback: types.CallbackQuery, state: FSMContext):
    if not AccessControl.is_admin(callback.from_user.id):
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return

    old_title = callback.data.split(":")[1]
    await state.update_data(old_title=old_title)
    await callback.message.answer(
        f"Введите новое название для '{old_title}':\n"
        "(Или отправьте /cancel для отмены)"
    )
    await callback.answer()
    await state.set_state(RenameStates.waiting_for_new_title)

@dp.callback_query(F.data.startswith("delete:"))
async def delete_voice_callback(callback: types.CallbackQuery):
    if not AccessControl.is_admin(callback.from_user.id):
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return

    title = callback.data.split(":")[1]
    if storage.delete_voice(title):
        await callback.message.answer(f"✅ Сообщение '{title}' удалено", reply_markup=get_main_keyboard())
    else:
        await callback.message.answer("❌ Не удалось удалить сообщение", reply_markup=get_main_keyboard())
    await callback.answer()

@dp.message(RenameStates.waiting_for_new_title)
async def handle_new_title(message: Message, state: FSMContext):
    if message.text.startswith('/'):
        await message.reply("❌ Используйте текстовое сообщение для нового названия")
        return

    data = await state.get_data()
    old_title = data.get('old_title')
    new_title = message.text.strip()

    if not old_title:
        await message.reply("❌ Ошибка: исходное сообщение не найдено", reply_markup=get_main_keyboard())
        await state.clear()
        return

    if len(new_title) > 32:  # MAX_TITLE_LENGTH
        await message.reply("❌ Слишком длинное название (максимум 32 символа)")
        return

    if storage.rename_voice(old_title, new_title):
        await message.reply(
            f"✅ Успешно переименовано с '{old_title}' на '{new_title}'",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.reply(
            "❌ Не удалось переименовать. Возможные причины:\n"
            "- Такое название уже существует\n"
            "- Исходное сообщение было удалено",
            reply_markup=get_main_keyboard()
        )

    await state.clear()

# ==============================================
# Инлайн-режим
# ==============================================

@dp.inline_query()
async def inline_voices(query: InlineQuery):
    if not AccessControl.is_user(query.from_user.id):
        await query.answer(
            results=[],
            switch_pm_text="Доступ запрещён. Запросить доступ?",
            switch_pm_parameter="request_access",
            cache_time=300
        )
        return

    search_query = query.query.strip().lower()
    results = []

    for idx, (title, file_id) in enumerate(storage.get_all_voices()):
        if search_query and not title.lower().startswith(search_query):
            continue

        results.append(
            InlineQueryResultVoice(
                id=str(idx),
                voice_file_id=file_id,
                title=title,
                voice_url=""
            )
        )

        if len(results) >= 50:
            break

    await query.answer(results, cache_time=0, is_personal=True)
    
# ======================
# Управление админами
# ======================

@dp.message(F.text == "👑 Управление админами")
async def manage_admins(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        return
    
    await message.answer(
        "Управление администраторами:",
        reply_markup=get_admin_management_keyboard()
    )

@dp.message(F.text == "📋 Список админов")
async def list_admins(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        return
    
    admins = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    response = ["👑 Список администраторов:"]
    
    for admin_id in admins:
        user_info = await get_user_display_info(admin_id)
        response.append(f"• {user_info}")
    
    if not admins:
        response.append("❌ Нет администраторов")
    
    await message.answer("\n".join(response))

def get_admins() -> list[int]:
    """Возвращает текущий список ID администраторов"""
    load_dotenv()  # Перезагружаем .env
    admin_ids = os.getenv("ADMIN_IDS", "")
    return [int(id) for id in admin_ids.split(",") if id.strip()]

def update_admins(admin_ids: list[int]):
    """Обновляет список администраторов в .env"""
    admins_str = ",".join(map(str, admin_ids))
    # Читаем текущее содержимое .env
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Перезаписываем файл, обновляя только ADMIN_IDS
    with open('.env', 'w') as f:
        admin_updated = False
        for line in lines:
            if line.startswith("ADMIN_IDS="):
                f.write(f"ADMIN_IDS={admins_str}\n")
                admin_updated = True
            elif not line.strip().startswith("#") and "=" in line:  # Сохраняем другие переменные
                f.write(line)
        
        if not admin_updated:
            f.write(f"ADMIN_IDS={admins_str}\n")

@dp.message(F.text == "➕ Добавить админа")
async def add_admin_start(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN:
        return
    
    await message.answer(
        "Введите ID или @username нового администратора:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminStates.waiting_admin_id)

@dp.message(AdminStates.waiting_admin_id)
async def add_admin_finish(message: Message, state: FSMContext):
    try:
        user_input = message.text.strip()
        user_id = None
        
        # Обработка ввода username
        if user_input.startswith("@"):
            try:
                user = await bot.get_chat(user_input)
                user_id = user.id
            except Exception:
                await message.answer("❌ Не удалось найти пользователя. Введите ID вручную")
                return
        else:
            try:
                user_id = int(user_input)
            except ValueError:
                await message.answer("❌ Неверный формат. Введите ID или @username")
                return
        
        admins = get_admins()
        
        if user_id in admins:
            await message.answer("❌ Этот пользователь уже администратор")
            return
        
        admins.append(user_id)
        update_admins(admins)
        reload_env_vars()  # Перезагружаем переменные
        
        user_info = await get_user_display_info(user_id)
        await message.answer(
            f"✅ {user_info} добавлен как администратор",
            reply_markup=get_admin_management_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка добавления админа: {e}")
        await message.answer("❌ Ошибка при добавлении")
    finally:
        await state.clear()

@dp.message(F.text == "➖ Удалить админа")
async def remove_admin_start(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        return
    
    admins = get_admins()
    
    if not admins:
        await message.answer("❌ Нет администраторов для удаления")
        return
    
    builder = InlineKeyboardBuilder()
    for admin_id in admins:
        user_info = await get_user_display_info(admin_id)
        builder.button(
            text=user_info,
            callback_data=f"remove_admin:{admin_id}"
        )
    builder.adjust(1)
    
    await message.answer(
        "Выберите администратора для удаления:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("remove_admin:"))
async def remove_admin_callback(callback: CallbackQuery):
    if callback.from_user.id != SUPER_ADMIN:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    
    try:
        admin_id = int(callback.data.split(":")[1])
        admins = get_admins()
        
        if admin_id in admins:
            admins.remove(admin_id)
            update_admins(admins)
            reload_env_vars()  # Перезагружаем переменные
            
            user_info = await get_user_display_info(admin_id)
            await callback.message.edit_text(f"✅ {user_info} удален из администраторов")
        else:
            await callback.message.edit_text("❌ Администратор не найден")
            
    except Exception as e:
        logger.error(f"Ошибка удаления админа: {e}")
        await callback.message.edit_text("❌ Ошибка при удалении")
    finally:
        await callback.answer()

# ======================
# Управление говорунами
# ======================

@dp.message(F.text == "🗣 Управление говорунами")
async def manage_speakers(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        return
    
    await message.answer(
        "Управление говорунами:",
        reply_markup=get_speaker_management_keyboard()
    )

@dp.message(F.text == "📋 Список говорунов")
async def list_speakers(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        return
    
    users = [int(id) for id in os.getenv("USER_IDS", "").split(",") if id]
    response = ["🗣 Список говорунов:"]
    
    for user_id in users:
        user_info = await get_user_display_info(user_id)
        response.append(f"• {user_info}")
    
    if not users:
        response.append("❌ Нет говорунов")
    
    await message.answer("\n".join(response))

def get_users() -> list[int]:
    """Возвращает текущий список ID пользователей"""
    load_dotenv()
    user_ids = os.getenv("USER_IDS", "")
    return [int(id) for id in user_ids.split(",") if id.strip()]

def update_users(user_ids: list[int]):
    """Обновляет список пользователей в .env"""
    users_str = ",".join(map(str, user_ids))
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    with open('.env', 'w') as f:
        users_updated = False
        for line in lines:
            if line.startswith("USER_IDS="):
                f.write(f"USER_IDS={users_str}\n")
                users_updated = True
            elif not line.strip().startswith("#") and "=" in line:
                f.write(line)
        
        if not users_updated:
            f.write(f"USER_IDS={users_str}\n")

@dp.message(F.text == "➕ Добавить говоруна")
async def add_speaker_start(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN:
        return
    
    await message.answer(
        "Введите ID или @username нового говоруна:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminStates.waiting_speaker_id)

@dp.message(AdminStates.waiting_speaker_id)
async def add_speaker_finish(message: Message, state: FSMContext):
    try:
        user_input = message.text.strip()
        user_id = None
        
        if user_input.startswith("@"):
            try:
                user = await bot.get_chat(user_input)
                user_id = user.id
            except Exception:
                await message.answer("❌ Не удалось найти пользователя. Введите ID вручную")
                return
        else:
            try:
                user_id = int(user_input)
            except ValueError:
                await message.answer("❌ Неверный формат. Введите ID или @username")
                return
        
        users = get_users()
        
        if user_id in users:
            await message.answer("❌ Этот пользователь уже имеет доступ")
            return
        
        users.append(user_id)
        update_users(users)
        reload_env_vars()  # Перезагружаем переменные
        
        user_info = await get_user_display_info(user_id)
        await message.answer(
            f"✅ {user_info} добавлен как говорун",
            reply_markup=get_speaker_management_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка добавления говоруна: {e}")
        await message.answer("❌ Ошибка при добавлении")
    finally:
        await state.clear()

@dp.message(F.text == "➖ Удалить говоруна")
async def remove_speaker_start(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        return
    
    users = get_users()
    
    if not users:
        await message.answer("❌ Нет говорунов для удаления")
        return
    
    builder = InlineKeyboardBuilder()
    for user_id in users:
        user_info = await get_user_display_info(user_id)
        builder.button(
            text=user_info,
            callback_data=f"remove_speaker:{user_id}"
        )
    builder.adjust(1)
    
    await message.answer(
        "Выберите говоруна для удаления:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("remove_speaker:"))
async def remove_speaker_callback(callback: CallbackQuery):
    if callback.from_user.id != SUPER_ADMIN:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    
    try:
        user_id = int(callback.data.split(":")[1])
        users = get_users()
        
        if user_id in users:
            users.remove(user_id)
            update_users(users)
            reload_env_vars()  # Перезагружаем переменные
            
            user_info = await get_user_display_info(user_id)
            await callback.message.edit_text(f"✅ {user_info} удален из говорунов")
        else:
            await callback.message.edit_text("❌ Говорун не найден")
            
    except Exception as e:
        logger.error(f"Ошибка удаления говоруна: {e}")
        await callback.message.edit_text("❌ Ошибка при удалении")
    finally:
        await callback.answer()

# ======================
# Навигация
# ======================

@dp.message(F.text == "🔙 Назад")
async def back_to_admin_main(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        return
    
    await message.answer(
        "Панель управления:",
        reply_markup=get_admin_main_keyboard()
    )

@dp.message(F.text == "🔙 Главное меню")
async def back_to_main_menu(message: Message):
    if message.from_user.id != SUPER_ADMIN:
        return
    
    await message.answer(
        "Главное меню:",
        reply_markup=ReplyKeyboardRemove()
    )

# ======================
# Запуск бота
# ======================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
