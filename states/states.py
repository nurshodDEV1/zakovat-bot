from aiogram.fsm.state import State, StatesGroup

class RegistrationState(StatesGroup):
    waiting_for_contact = State()

class GameState(StatesGroup):
    waiting_for_answer = State()

class AdminState(StatesGroup):
    waiting_for_question_text = State()
    waiting_for_answer_text = State()
    waiting_for_explanation = State()
