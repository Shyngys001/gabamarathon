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

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# 🔄 FSM Состояния
class OrderState(StatesGroup):
    waiting_for_payment = State()
    waiting_for_receipt = State()
    waiting_for_name = State()
    waiting_for_phone = State()

# 🔔 Список возражений
OBJECTION_MESSAGES = [
    "❗ <b>Мен тырысып көрдім, бірақ маған ештеңе көмектеспейді</b>\n\n"
    "➡ Бұрынғы әдістеріңіз нәтиже бермесе, бұл дұрыс жолмен арықтамағаныңызды білдіреді. "
    "Менің әдістемем басқа:\n"
    "✔️ Бұл диета емес, аш қалу емес, қатаң шектеу емес.\n"
    "✔️ Сіз денеңіздің табиғи арықтау процесін қосасыз – ол өздігінен майларды кетіре бастайды.\n"
    "✔️ Мыңдаған адамға көмектескен жүйе сізге де жұмыс істейді!",

    "❗ <b>Менде мотивация жетіспейді</b>\n\n"
    "➡ Сондықтан сізге марафон керек! Жалғыз бастасаңыз, мотивацияңыз тез өшіп қалады. "
    "Ал марафонда мен сізді күн сайын бағыттаймын, мотивация беремін. Сіз жалғыз емессіз!",

    "❗ <b>Маған уақыт тапшы, жұмысым көп</b>\n\n"
    "➡ Марафон уақыт алмайды! Күнделікті тапсырмалар оңай, оларды өз өміріңізге бейімдеп жасайсыз. "
    "Қатаң режим жоқ!",

    "❗ <b>1000 теңгеге не үйренем? Тегін болса қатысар едім</b>\n\n"
    "➡ 1000 тг – бір шыны кофе бағасы. Ал марафон сізге денсаулық, әдемі дене, жеңілдік сезімін береді. "
    "Тегін нәрсені адам қадірлемейді, ал сіз осы 1000 тг арқылы өзіңізге үлкен өзгеріс жасағыңыз келетінін дәлелдейсіз.",

    "❗ <b>Спортсыз арықтау мүмкін емес</b>\n\n"
    "➡ Иә, спорт пайдалы, бірақ арықтаудың 80%-ы дұрыс тамақтану мен метаболизмді реттеуге байланысты. "
    "Спортсыз-ақ май кетеді!"
]

# 📢 Стартовое сообщение
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

# 📌 Обработка "✅ Видеоны көрдім"
@dp.callback_query(lambda c: c.data == "watched_video")
async def ask_payment(callback: types.CallbackQuery, state: FSMContext):
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
    
    await callback.message.answer(text, reply_markup=keyboard)
    await state.set_state(OrderState.waiting_for_payment)
    asyncio.create_task(send_payment_reminders(callback.from_user.id, state))  # Запуск напоминаний
    await callback.answer()

# 🔄 Функция для отправки возражений при напоминании
async def send_payment_reminders(user_id, state: FSMContext):
    for i in range(10):  # 10 раз отправит напоминание (20 минут)
        await asyncio.sleep(120)  # Ждать 2 минуты
        current_state = await state.get_state()
        if current_state != OrderState.waiting_for_payment:
            break  # Если клиент оплатил, прекращаем напоминания

        objection_text = OBJECTION_MESSAGES[i % len(OBJECTION_MESSAGES)]  # Выбираем возражение по очереди

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

# 📩 Запрос чека, затем запроса имени
@dp.message(OrderState.waiting_for_receipt)
async def ask_name_after_receipt(message: types.Message, state: FSMContext):
    # Сохранение чека
    if message.photo:
        file_id = message.photo[-1].file_id
        await bot.send_photo(ADMIN_ID, file_id, caption="💳 Жаңа чек келді!")
    elif message.document:
        file_id = message.document.file_id
        await bot.send_document(ADMIN_ID, file_id, caption="💳 Жаңа чек келді!")
    else:
        await bot.send_message(ADMIN_ID, f"💳 Жаңа чек келді!\n{message.text}")

    # Переход к запросу имени
    await message.answer("📌 Атыңыз кім?")
    await state.set_state(OrderState.waiting_for_name)

# 📞 Запрос номера телефона после имени
@dp.message(OrderState.waiting_for_name)
async def ask_phone(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📞 Телефон нөміріңіз?")
    await state.set_state(OrderState.waiting_for_phone)

# ✅ Обработка номера телефона и отправка админу
@dp.message(OrderState.waiting_for_phone)
async def save_client_data(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data.get("name", "Анықталмаған")
    phone = message.text

    admin_text = f"""🔔 <b>Жаңа төлем!</b>

👤 Аты: {name}
📞 Телефон: {phone}"""
    
    await bot.send_message(ADMIN_ID, admin_text)
    await message.answer("🎉 Төлем қабылданды! Ұйымдастырушылар сізді топқа қосады.")
    await state.clear()

# 🚀 Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())