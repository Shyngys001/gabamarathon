import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = "7859736492:AAGhN-jAfsjYnkyDIjf2CHdcRrztwl9jIZM"
ADMIN_ID = "1050963411"
PAYMENT_URL = "https://pay.kaspi.kz/pay/iyzblpte"
VIDEO_URL = "https://shyngys001.github.io/gabitmarathon/"

# Создание бота и диспетчера с передачей parse_mode
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# 🔄 FSM Состояния
class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_payment = State()
    waiting_for_receipt = State()

# 📢 Стартовое сообщение с кнопками
@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📺 Видеоны көру", url=VIDEO_URL)],
        [InlineKeyboardButton(text="✅ Видеоны көрдім", callback_data="watched_video")]
    ])

    text = """<b>7 күнде 7 кг тастағың келе ме?</b>

❌ Диета жоқ
❌ Аштық жоқ
❌ Спортзалдың керегі жоқ

✅ Күніне 10-15 минуттық жеңіл әдістер
✅ Организмге қауіпсіз жүйе
✅ 1000+ адамның нәтиже алған тәсілі

Тегін видеоны көріп, бүгіннен бастап арықтауды баста!"""
    
    await message.answer(text, reply_markup=keyboard)
    await state.clear()

# 📌 Обработка "✅ Видеоны көрдім"
@dp.callback_query(lambda c: c.data == "watched_video")
async def ask_name(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📌 Атыңыз кім?")
    await state.set_state(OrderState.waiting_for_name)
    await callback.answer()

# 📞 Получение имени и запрос номера телефона
@dp.message(OrderState.waiting_for_name)
async def ask_phone(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📞 Телефон нөміріңіз?")
    await state.set_state(OrderState.waiting_for_phone)

# 💳 Запрос на оплату
@dp.message(OrderState.waiting_for_phone)
async def ask_payment(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Төлеу", url=PAYMENT_URL)],
        [InlineKeyboardButton(text="✅ Төледім", callback_data="paid")]
    ])

    text = """<b>Нәтижеге 7 қадам қалды!</b>

⚡ 7 күнде 7 кг тастау марафонына қосыл! ⚡
✅ Күнделікті дайын жоспар
✅ Бар-жоғы 10-15 минуттық әдістер
✅ Аштық пен қатаң диетасыз жүйе
✅ Нақты нәтиже алған 1000+ адамның әдісі

Бүгін бастағандар – 7 күннен кейін айнадан өзіне риза болады!

<b>Орныңды ал – бар болғаны 3000 тг!</b>"""
    
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(OrderState.waiting_for_payment)

# ✅ Обработка "Төледім"
@dp.callback_query(lambda c: c.data == "paid")
async def confirm_payment(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📌 Чек жіберіңіз.")
    await state.set_state(OrderState.waiting_for_receipt)
    await callback.answer()

# 📩 Сохранение данных клиента
@dp.message(OrderState.waiting_for_receipt)
async def save_client_data(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data.get("name", "Анықталмаған")
    phone = user_data.get("phone", "Анықталмаған")
    receipt = message.text

    # Отправка данных админу
    admin_text = f"""🔔 <b>Жаңа төлем!</b>

👤 Аты: {name}
📞 Телефон: {phone}
💳 Чек: {receipt}"""
    
    await bot.send_message(ADMIN_ID, admin_text)
    await message.answer("🎉 Төлем қабылданды! Ұйымдастырушылар сізді топқа қосады.")

    await state.clear()

# 🚀 Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())