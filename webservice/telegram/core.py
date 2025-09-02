# импорт модулей
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from dotenv import load_dotenv
import os
import aiohttp
from datetime import datetime, timedelta
import ssl

# настройки самоподписанного сертификата
# создание клиентского SSL-контекста
ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
# указываем пути к сертификату и ключу (если это требуется для твоего клиента)
ssl_context.load_cert_chain(certfile="/etc/ssl/server.pem", keyfile="/etc/ssl/private/server.key")
# отключи валидацию сертификата сервера
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# загружаем переменные окружения
load_dotenv()

# токен бота
TOKEN = os.getenv('tg_token')

# Порог неактивности для завершения сессии
INACTIVITY_TIMEOUT = timedelta(minutes=10)

# функция-обработчик команды /start
async def start(update, context):
    user_id = update.message.from_user.id
    # Инициализируем данные пользователя, если их еще нет
    if user_id not in context.bot_data:
        context.bot_data[user_id] = {'remaining_requests': 3, 'last_active': datetime.now()}
    await update.message.reply_text('Привет! Меня зовут Лиза, я консультант компании Atomy. Могу я чем-то вам помочь?')

# функция-обработчик текстовых сообщений
async def text(update, context):
    user_id = update.message.from_user.id
    # Обновляем время последнего действия
    if user_id not in context.bot_data:
        context.bot_data[user_id] = {'remaining_requests': 3, 'last_active': datetime.now()}
    context.bot_data[user_id]['last_active'] = datetime.now()

    # Проверяем лимит обращений
    if context.bot_data[user_id]['remaining_requests'] > 0:
        param = {'text': update.message.text}
        async with aiohttp.ClientSession() as session:
            async with session.post('https://5.188.200.90:443/api/get_answer_async', json=param, ssl=ssl_context) as response:
                answer = await response.json()
                # Уменьшаем количество доступных запросов
                context.bot_data[user_id]['remaining_requests'] -= 1
                answer['message'] += f'\n-\nУ вас осталось обращений: {context.bot_data[user_id]["remaining_requests"]}'
                await update.message.reply_text(answer['message'])
    else:
        await update.message.reply_text('Ваш лимит 3 обращения в 10 минут. На текущий момент исчерпан!')

# Функция срабатывает через заданный интервал времени
async def task(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    inactive_users = []

    # Проверяем все активные сессии
    for user_id, user_data in context.bot_data.items():
        # Если пользователь был неактивен больше INACTIVITY_TIMEOUT
        if now - user_data['last_active'] > INACTIVITY_TIMEOUT:
            inactive_users.append(user_id)

    # Удаляем данные неактивных пользователей
    for user_id in inactive_users:
        del context.bot_data[user_id]
        print(f"Данные пользователя {user_id} удалены из-за неактивности.")

    # Сбрасываем лимиты для активных пользователей
    for user_id, user_data in context.bot_data.items():
        user_data['remaining_requests'] = 3
    print('Лимиты обновлены для активных пользователей.')

# функция "Запуск бота"
def main():
    # создаем приложение и передаем в него токен
    application = Application.builder().token(TOKEN).build()

    # запуск планировщика
    schedule = application.job_queue
    interval = 60 * 10 # проверка каждые 600 секунд
    schedule.run_repeating(task, interval=interval)

    # добавляем обработчик команды /start
    application.add_handler(CommandHandler('start', start))

    # добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, text))

    # запускаем бота
    print('Бот запущен...')
    application.run_polling()
    print('Бот остановлен')

# проверяем режим запуска модуля
if __name__ == "__main__":
    main()
