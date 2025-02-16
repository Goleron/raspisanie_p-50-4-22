import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
import requests
from bs4 import BeautifulSoup
import asyncio

logging.basicConfig(level=logging.INFO)

API_TOKEN = '7765583170:AAFTkKyFkr49khxXhW7w8dgS-VdWjTMbbz0'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

CHAT_ID = None

# Статичные данные расписания 
schedule_numerator = {
    "Понедельник": ["Разработка программных модулей(Парамонова)", "Разработка программных модулей(Подлесный)", "Менеджмент в профессиональной деятельности(Кицына)"],
    "Вторник": ["Менеджмент в профессиональной деятельности(Кицына)", "Системное программирование(Чернышев)", "Разработка программных модулей(Осипян)", "Технология разработки и защиты баз данных(Архангельский)"],
    "Четверг": ["Стандартизация, сертификация и тех. документоведение(Каминьски)", "Системное программирование(Чернышев)", "Инструментальные средства разработки ПО(Юшина)", "Технология разработки программного обеспечения(Волков)"],
    "Пятница": ["Физическая культура(Андрюков)", "Стандартизация, сертификация и тех. документоведение(Осипян)", "Разработка мобильных приложений(Никонова)"],
    "Суббота": ["Разработка мобильных приложений(Никонова)", "Технология разработки и защиты баз данных(Перевалов)", "Иностранный язык в профессиональной деятельности(Дымская, Афанасьева)", "Технология разработки программного обеспечения(Волков)"]
}

schedule_denominator = {
    "Понедельник": ["Разработка программных модулей(Парамонова)", "Разработка программных модулей(Подлесный)", "Менеджмент в профессиональной деятельности(Кицына)"],
    "Вторник": ["Разработка программных модулей(Парамонова)", "Системное программирование(Чернышев)", "Разработка программных модулей(Осипян)", "Технология разработки и защиты баз данных(Архангельский)"],
    "Четверг": ["Стандартизация, сертификация и тех. документоведение(Каминьски)", "Системное программирование(Чернышев)", "Инструментальные средства разработки ПО(Юшина)", "Технология разработки программного обеспечения(Волков)"],
    "Пятница": ["Физическая культура(Андрюков)", "Стандартизация, сертификация и тех. документоведение(Осипян)", "Разработка мобильных приложений(Никонова)"],
    "Суббота": ["Разработка мобильных приложений(Никонова)", "Технология разработки и защиты баз данных(Перевалов)", "Иностранный язык в профессиональной деятельности(Дымская, Афанасьева)", "Инструментальные средства разработки ПО(Юшина)"]
}

# Функция для определения текущей недели (числитель/знаменатель)
def get_current_week():
    url = 'https://mpt.ru/raspisanie/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    week_info = soup.find('div', class_='col-xs-12 col-sm-12 col-md-12').text.strip()  # Ищем информацию о неделе
    if "числитель" in week_info.lower():
        return "числитель"
    elif "знаменатель" in week_info.lower():
        return "знаменатель"
    else:
        return None

# Функция для получения изменений в расписании
def get_schedule_changes():
    url = 'https://mpt.ru/izmeneniya-v-raspisanii/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('div', class_='table-responsive')
    if not tables:
        return "Изменений в расписании нет."
    changes = []
    for table in tables:
        caption = table.find('caption')
        if caption and 'П50-4-22' in caption.text:
            rows = table.find_all('tr')[1:]
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 3:
                    lesson_number = columns[0].text.strip()
                    replace_from = columns[1].text.strip()
                    replace_to = columns[2].text.strip()
                    updated_at = columns[3].text.strip() if len(columns) > 3 else "Не указано"
                    changes.append(f"Пара {lesson_number}: {replace_from} → {replace_to} (Обновлено: {updated_at})")
    if not changes:
        return "Изменений в расписании для группы П50-4-22 нет."
    result = f"Изменения в расписании для группы П50-4-22:\n\n" + "\n".join(changes)
    return result

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    global CHAT_ID
    CHAT_ID = message.chat.id  # Сохраняем CHAT_ID пользователя
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text='Расписание')],
            [types.KeyboardButton(text='Изменения в расписании')]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите действие:", reply_markup=keyboard)

# Обработка кнопки "Расписание"
@dp.message(lambda message: message.text == 'Расписание')
async def send_schedule(message: types.Message):
    current_week = get_current_week()
    if current_week == "числитель":
        schedule = schedule_numerator
    elif current_week == "знаменатель":
        schedule = schedule_denominator
    else:
        await message.answer("Не удалось определить текущую неделю.")
        return
    response = "📅 Текущее расписание:\n"
    for day, subjects in schedule.items():
        response += f"\n{day}:\n"
        for i, subject in enumerate(subjects, 1):
            response += f"{i}. {subject}\n"
    await message.answer(response, parse_mode=ParseMode.MARKDOWN)

# Обработка кнопки "Изменения в расписании"
@dp.message(lambda message: message.text == 'Изменения в расписании')
async def send_changes(message: types.Message):
    changes = get_schedule_changes()
    await message.answer(changes, parse_mode=ParseMode.MARKDOWN)


async def scheduled(wait_for):
    global CHAT_ID
    last_changes = None
    while True:
        await asyncio.sleep(wait_for)
        changes = get_schedule_changes()
        if changes and changes != last_changes:
            last_changes = changes
            if CHAT_ID: 
                await bot.send_message(chat_id=CHAT_ID, text=f"📢 Обновление в расписании:\n{changes}")

# Запуск бота
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled(3600)) 
    loop.run_until_complete(dp.start_polling(bot))