# tg_bot
just for me in case i forget smthng. why its not private then? so I look like cool guy (not rly)

main code in bot.py
voices.json store tg voice key, number
voices_storage controls for voice list managing
video_processor allows convert video in voice message
states becouse deepseek did so
keyboards for buttons and icons
access_control for access control :D user - admin - superadmin

launch in venv ,

requierments -  aiogram==3.0.0b7
                python-dotenv==1.0.0
                ffmpeg-python==0.2.0
                requests==2.31.0
(? asyncio ?)

to make bot working you need .env with theese:

BOT_TOKEN=21312321:xdfasdf2131
SUPER_ADMIN=123123123
ADMIN_IDS=12345678,87654321,54257312
USER_IDS=1221323678,87323421,542445643
LOG_CHANNEL_ID=@anychat
