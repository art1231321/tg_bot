import os
import subprocess
import logging
from typing import Optional
from aiogram.types import BufferedInputFile, Message

logger = logging.getLogger(__name__)

async def convert_video_to_voice(message: Message, temp_dir: str = "temp") -> Optional[str]:
    """Конвертирует видео в голосовое сообщение с корректной загрузкой файла"""
    try:
        # Проверяем тип сообщения
        if message.video:
            video = message.video
        elif message.video_note:
            video = message.video_note
        else:
            return None

        # Создаем временную директорию
        os.makedirs(temp_dir, exist_ok=True)
        
        # Скачиваем видео файл
        video_path = os.path.join(temp_dir, f"video_{message.from_user.id}.mp4")
        await message.bot.download(
            file=video.file_id,
            destination=video_path
        )

        # Конвертируем в аудио
        audio_path = os.path.join(temp_dir, f"audio_{message.from_user.id}.ogg")
        subprocess.run([
            'ffmpeg',
            '-i', video_path,
            '-vn',              # Без видео
            '-ac', '1',         # Моно звук
            '-ar', '16000',     # Частота дискретизации
            '-acodec', 'libopus', # Кодек Opus
            '-f', 'ogg',        # Формат OGG
            '-y',               # Перезаписать если существует
            audio_path
        ], check=True)

        # Читаем конвертированный файл
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        # Отправляем как голосовое сообщение
        voice_message = await message.bot.send_voice(
            chat_id=message.chat.id,
            voice=BufferedInputFile(
                file=audio_data,
                filename="converted_voice.ogg"
            ),
            disable_notification=True
        )

        return voice_message.voice.file_id

    except Exception as e:
        logger.error(f"Ошибка конвертации: {str(e)}")
        return None
    finally:
        # Удаляем временные файлы
        for file_path in [video_path, audio_path]:
            if 'file_path' in locals() and file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Ошибка удаления файла: {str(e)}")
