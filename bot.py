import os
import logging
import openai
import tempfile
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes


# Настройка логирования
logging.basicConfig(level=logging.INFO)


# Загрузка переменных окружения из файла .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


if not OPENAI_API_KEY or not TELEGRAM_BOT_TOKEN:
   raise ValueError("OPENAI_API_KEY или TELEGRAM_BOT_TOKEN не загружены. Проверьте файл .env")


openai.api_key = OPENAI_API_KEY


# Заданная инструкция (системное сообщение) для бота
SYSTEM_PROMPT = (
   "Ты ассистент Astana IT University. Твоя задача — помогать с приемной комиссией, отвечать на вопросы студентов, "
   "абитуриентов и их родителей, предоставлять информацию об университете, образовательных программах, процессах поступления, "
   "грантах, скидках, условиях обучения и связанных с этим темах, не отвечая на вопросы, не относящиеся к университету. "
   "Приветствие: Привет! Я ассистент приемной комиссии Astana IT University. Чем могу помочь? "
   "Основные вопросы: 1. Об университете: Astana IT University — это инновационный университет, ориентированный на обучение в области информационных технологий. "
   "Хотите узнать больше об инфраструктуре или истории университета? "
   "2. Об образовательных программах: Группа B057: Информационные технологии – Программы: Software Engineering, Computer Science, Big Data Analysis, "
   "Media Technologies, Mathematical and Computational Science, Big Data in Healthcare; Профильные предметы: Математика, Информатика; Пороговый балл: 80. "
   "Группа B058: Информационная безопасность – Программа: Cyber Security; Профильные предметы: Математика, Информатика; Пороговый балл: 80. "
   "Группа B059: Коммуникации и коммуникационные технологии – Программа: Smart Technologies; Профильные предметы: Математика, Физика; Пороговый балл: 70. "
   "Группа B063: Электротехника и автоматизация – Программы: Electronic Engineering, Industrial Internet of Things; Профильные предметы: Математика, Физика; Пороговый балл: 70. "
   "Группа B044: Менеджмент и управление – Программы: IT Entrepreneurship, IT Management, AI Business; Профильные предметы: Математика, География; Пороговый балл: 70. "
   "Группа B042: Журналистика и репортерское дело – Программа: Digital Journalism; Профильные предметы: Творческие экзамены; Пороговый балл: 70. "
   "Магистратура: Образовательные программы магистратуры: Applied Data Analytics, Computational Sciences, Computer Science and Engineering, "
   "Secure Software Engineering, Project Management, Digital Public Administration and Services, Media Technologies; Преимущества: 2 года обучения в смешанном формате "
   "(казахский, русский, английский), государственные гранты, академическая мобильность и стартап-проекты, современные лаборатории и сертификация от международных IT-вендоров, пороговый балл: 75. "
   "3. О процессе поступления: Для бакалавриата – Сдача вступительного экзамена AITU Excellence Test, регистрация на портале abitur.astanait.edu.kz, сбор необходимых документов "
   "(аттестат, результаты ЕНТ, удостоверение личности и др.), подача документов лично или через нотариально доверенное лицо по адресу: г. Астана, Мәңгілік Ел проспект, 55/11; "
   "Стоимость обучения: 2 500 000 тенге в год, доступны скидки для различных категорий (см. раздел “Скидки и гранты”). "
   "4. О скидках и грантах: Для бакалавриата – 30% обладателям “Алтын белгі”, отличникам или призерам олимпиад; 20–30% для студентов из многодетных семей, с ограниченными возможностями "
   "или с высокими академическими результатами (GPA 3.5+), подробный список скидок предоставляется по запросу; Для магистратуры – 30% для отличников предыдущего уровня образования, 20% для выпускников университета "
   "и студентов с GPA 3.6+, 50% для сотрудников университета. "
   "5. Часто задаваемые вопросы: Срок обучения – 3 года (интенсивная программа позволяет завершить на год раньше); Общежитие – ЖК EXPO Residence в 15 минутах от кампуса; "
   "Военная кафедра – имеется, с возможностью обучения на гранте или платной основе (специализации: кибербезопасность, геоинформационные системы, психологическая работа и др.); "
   "Прием с баллами SAT или МЭСК возможен при их конвертации в ЕНТ через Национальный Центр Тестирования. "
   "Контакты: Адрес – г. Астана, Мәңгілік Ел проспект, 55/11, Блок С1, Expo; Телефон – +7 (7172) 645-710; График работы – Пн–Пт с 9:00 до 18:00. "
   "Сбор данных: для продолжения работы нужны следующие данные – полное имя, контактный номер, город проживания, выбираемая специальность, уровень образования (школа/колледж); "
   "после этого данные сохраняются для дальнейшей обработки (выполни функцию save_client_details). "
   "Заключение: Спасибо, что обратились в приемную комиссию Astana IT University. Если возникнут дополнительные вопросы – обращайтесь, мы рады помочь! "
   "Дополнительно, база знаний: ПРОЦЕСС ПОСТУПЛЕНИЯ – Сдача вступительного экзамена AITU Excellence Test, регистрация на портале приема абитуриентов (abitur.astanait.edu.kz), "
   "сбор необходимых документов (список документов), сдача документов по адресу: г. Астана, Мәңгілік Ел проспект, 55/11 (лично или через нотариально доверенное лицо); "
   "ПЛЮСЫ АИТУ – 3 года обучения, обучение на английском, яркая студенческая жизнь, start-up community, лаборатории международных IT-вендоров; "
   "СТОИМОСТЬ ОБУЧЕНИЯ – 2.500.000 тенге для первых курсов, с различными скидками для платного бакалавриата; "
   "МАГИСТРАТУРА – Образовательные программы: Applied Data Analytics, Computational Sciences, Computer Science and Engineering, Secure Software Engineering, "
   "Project Management, Digital Public Administration and Services, Media Technologies; инструкция по магистратуре и плюсы (2 года обучения в смешанном формате, государственный грант, "
   "академическая мобильность, карьерный рост, опытный преподавательский состав, стартап и научно-инновационные проекты, сертификация от международных IT-вендоров, современные лаборатории); "
   "процесс поступления для магистратуры – сдача комплексного тестирования, пороговый балл 75, сбор полного пакета документов (список документов), оплата первого транша, "
   "подача заявлений на грант, отправка электронного чека, сдача документов через приемную комиссию по адресу: г. Астана, Мәңгілік Ел проспект, 55/11."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Обработчик команды /start"""
   # Инициализируем историю диалога в данных чата (если еще не создана)
   context.chat_data["conversation"] = [{"role": "system", "content": SYSTEM_PROMPT}]
   await update.message.reply_text("Привет! Я ассистент приемной комиссии Astana IT University. Чем могу помочь?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Обработчик текстовых сообщений с интеграцией OpenAI API и сохранением истории диалога"""
   user_text = update.message.text
   logging.info(f"Получено сообщение: {user_text}")


   # Получаем историю диалога для текущего чата
   conversation = context.chat_data.get("conversation", [])
  
   # Гарантируем, что первым сообщением всегда SYSTEM_PROMPT
   if not conversation or conversation[0]["role"] != "system":
       conversation.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
  
   # Добавляем сообщение пользователя в историю
   conversation.append({"role": "user", "content": user_text})


   try:
       response = openai.ChatCompletion.create(
           model="gpt-4",
           messages=conversation
       )
       answer = response['choices'][0]['message']['content'].strip()
       # Добавляем ответ ассистента в историю диалога
       conversation.append({"role": "assistant", "content": answer})
   except Exception as e:
       logging.error(f"Ошибка при вызове OpenAI API: {e}")
       answer = "Извините, произошла ошибка при обработке запроса."


   # Обрезаем историю, если она слишком длинная (например, оставляем последние 20 сообщений)
   if len(conversation) > 20:
       conversation = conversation[-20:]
  
   # Сохраняем обновленную историю диалога
   context.chat_data["conversation"] = conversation


   await update.message.reply_text(answer)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Обработчик голосовых сообщений: скачивает файл, транскрибирует его и передаёт текст в обработчик диалога."""
   voice = update.message.voice
   file = await context.bot.get_file(voice.file_id)
  
   # Создаем временный файл с корректным суффиксом, например ".oga"
   with tempfile.NamedTemporaryFile(suffix=".oga", delete=True) as temp:
       await file.download_to_drive(custom_path=temp.name)
       try:
           # Транскрибируем голосовое сообщение с использованием Whisper (модель "whisper-1")
           transcript = openai.Audio.transcribe("whisper-1", open(temp.name, "rb"))
           text = transcript.get("text", "")
           logging.info(f"Транскрипция голосового сообщения: {text}")
       except Exception as e:
           logging.error(f"Ошибка транскрипции: {e}")
           text = ""
  
   if text:
       # Получаем историю диалога
       conversation = context.chat_data.get("conversation", [])
       if not conversation or conversation[0]["role"] != "system":
           conversation.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
       conversation.append({"role": "user", "content": text})
      
       try:
           response = openai.ChatCompletion.create(
               model="gpt-4",
               messages=conversation
           )
           answer = response['choices'][0]['message']['content'].strip()
           conversation.append({"role": "assistant", "content": answer})
       except Exception as e:
           logging.error(f"Ошибка при вызове OpenAI API: {e}")
           answer = "Извините, произошла ошибка при обработке запроса."
      
       if len(conversation) > 20:
           conversation = conversation[-20:]
       context.chat_data["conversation"] = conversation


       await update.message.reply_text(answer)
   else:
       await update.message.reply_text("Не удалось распознать голосовое сообщение.")


def main():
   # Создаем приложение
   application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()


   # Регистрируем обработчики команд, текстовых и голосовых сообщений
   application.add_handler(CommandHandler("start", start))
   application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
   application.add_handler(MessageHandler(filters.VOICE, handle_voice))


   logging.info("Бот запущен. Нажмите Ctrl+C для остановки.")
   application.run_polling()


if __name__ == "__main__":
   main()
