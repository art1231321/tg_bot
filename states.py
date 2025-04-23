from aiogram.fsm.state import State, StatesGroup

class RenameStates(StatesGroup):
    waiting_for_new_title = State()

class AccessStates(StatesGroup):
    waiting_for_access_reason = State()

class AdminStates(StatesGroup):
    waiting_admin_id = State()
    waiting_speaker_id = State()
