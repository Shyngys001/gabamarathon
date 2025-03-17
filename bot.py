import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# 🔐 Конфигурация бота
TOKEN = "7859736492:AAGhN-jAfsjYnkyDIjf2CHdcRrztwl9jIZM"
ADMIN_ID = "306728906"
PAYMENT_URL = "https://pay.kaspi.kz/pay/iyzblpte"
VIDEO_URL = "https://shyngys001.github.io/gabitmarathon/"
SHEET_API_URL = "https://script.google.com/macros/s/AKfycbw5JdJPol9ZIwasv5fL3GLEK231Rl9-KQli35vrRX0vAZh_7jZceD9zwXPjpFP9X4tDvw/exec"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# 🔄 FSM Состояния
class OrderState(StatesGroup):
    waiting_for_payment = State()
    waiting_for_receipt = State()
    waiting_for_name = State()
    waiting_for_phone = State()

# 🔔 Сообщения для дожима
OBJECTION_MESSAGES = [
    "❗ <b>Мен тырысып көрдім, бірақ маған ештеңе көмектеспейді</b>\n\n➡ Бұрынғы әдістеріңіз нәтиже бермесе, бұл дұрыс жолмен арықтамағаныңызды білдіреді.",
    "❗ <b>Менде мотивация жетіспейді</b>\n\n➡ Сондықтан сізге марафон керек! Жалғыз бастасаңыз, мотивацияңыз тез өшіп қалады.",
    "❗ <b>Маған уақыт тапшы, жұмысым көп</b>\n\n➡ Марафон уақыт алмайды! Күнделікті тапсырмалар оңай, оларды өз өміріңізге бейімдеп жасайсыз.",
    "❗ <b>1000 теңгеге не үйренем? Тегін болса қатысар едім</b>\n\n➡ 1000 тг – бір шыны кофе бағасы. Ал марафон сізге денсаулық, әдемі дене, жеңілдік сезімін береді.",
    "❗ <b>Спортсыз арықтау мүмкін емес</b>\n\n➡ Иә, спорт пайдалы, бірақ арықтаудың 80%-ы дұрыс тамақтану мен метаболизмді реттеуге байланысты."
]

# 📢 Стартовое сообщение
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📺 Видеоны көру", url=VIDEO_URL)],
        [InlineKeyboardButton(text="✅ Видеоны көрдім", callback_data="watched_video")]
    ])

    text = "<b>7 күнде 7 кг тастағың келе ме?</b>\n\n❌ Диета жоқ\n❌ Аштық жоқ\n❌ Спортзалдың керегі жоқ\n\n✅ Күніне 10-15 минуттық жеңіл әдістер\n✅ Организмге қауіпсіз жүйе\n✅ 1000+ адамның нәтиже алған тәсілі"
    
    await message.answer(text, reply_markup=keyboard)

# 📌 Обработка "✅ Видеоны көрдім"
@dp.callback_query(lambda c: c.data == "watched_video")
async def ask_payment(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Төлеу", url=PAYMENT_URL)],
        [InlineKeyboardButton(text="✅ Төледім", callback_data="paid")]
    ])

    text = "<b>Нәтижеге 7 қадам қалды!</b>\n\n⚡ 7 күнде 7 кг тастау марафонына қосыл! ⚡\n✅ Күнделікті дайын жоспар\n✅ Бар-жоғы 10-15 минуттық әдістер\n✅ Аштық пен қатаң диетасыз жүйе"
    
    await callback.message.answer(text, reply_markup=keyboard)
    await state.set_state(OrderState.waiting_for_payment)
    asyncio.create_task(send_payment_reminders(callback.from_user.id, state))
    await callback.answer()

# 🔄 Функция для дожима (напоминания)
async def send_payment_reminders(user_id, state: FSMContext):
    for i in range(5):
        await asyncio.sleep(120)  # 2 минуты
        current_state = await state.get_state()
        if current_state != OrderState.waiting_for_payment:
            break
        objection_text = OBJECTION_MESSAGES[i % len(OBJECTION_MESSAGES)]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Төлеу", url=PAYMENT_URL)],
            [InlineKeyboardButton(text="✅ Төледім", callback_data="paid")]
        ])
        await bot.send_message(user_id, objection_text, reply_markup=keyboard)

# ✅ Обработка "Төледім"
@dp.callback_query(lambda c: c.data == "paid")
async def confirm_payment(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📌 Чек жіберіңіз (фото немесе PDF).")
    await state.set_state(OrderState.waiting_for_receipt)
    await callback.answer()

# 📩 Отправка чека админу, затем запрос имени
@dp.message(OrderState.waiting_for_receipt)
async def receive_receipt(message: types.Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        await bot.send_photo(ADMIN_ID, file_id, caption="💳 Жаңа чек келді!")
    elif message.document:
        file_id = message.document.file_id
        await bot.send_document(ADMIN_ID, file_id, caption="💳 Жаңа чек келді!")
    else:
        await bot.send_message(ADMIN_ID, f"💳 Жаңа чек келді!\n{message.text}")

    await message.answer("📌 Атыңыз кім?")
    await state.set_state(OrderState.waiting_for_name)

# 📞 Запрос номера телефона после имени
@dp.message(OrderState.waiting_for_name)
async def ask_phone(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📞 Телефон нөміріңіз?")
    await state.set_state(OrderState.waiting_for_phone)

# ✅ Сохранение данных в Google Sheets
@dp.message(OrderState.waiting_for_phone)
async def save_client_data(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data.get("name", "Анықталмаған")
    phone = message.text

    async with aiohttp.ClientSession() as session:
        await session.post(SHEET_API_URL, json={"name": name, "phone": phone})

    await bot.send_message(ADMIN_ID, f"🔔 Жаңа төлем!\n👤 Аты: {name}\n📞 Телефон: {phone}")
    await message.answer("🎉 Төлем қабылданды! Ұйымдастырушылар сізді топқа қосады.")
    await state.clear()

# 🚀 Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())