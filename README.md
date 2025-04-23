# tg_bot
> * just for me in case i forget smthng. why its not private then? so I look like cool guy (not rly) *

## Where what
- bot.py                  <sub>main code inside</sub>

- voices.json             <sub>store tg voice key, number</sub>

- voices_storage.py       <sub>controls for voice list managing</sub>

- video_processor.py     <sub> allows convert video in voice message</sub>

- states.py               <sub>becouse deepseek did so</sub>

- keyboards.py            <sub>for buttons and icons</sub>

- access_control.py       <sub>for access control :D user - admin - superadmin</sub>


## How to use
launch in venv ,

requierments - 

                aiogram==3.0.0b7
                
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


ofc u need to replace BOT_TOKEN by your own 😊

## TG bot setting?

inline_query must be turned on

I guess this is it...
