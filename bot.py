import telebot
import requests

TOKEN = "8426162475:AAFC888S2RaRcaujrZFXX4RcAdf8AY-O5hA"

# Создаём бота
bot = telebot.TeleBot(TOKEN)


# Функция сокращения ссылки через сервис is.gd (не требует регистрации!)
def shorten_url(long_url):
    try:
        # Отправляем запрос к is.gd
        response = requests.get(
            "https://is.gd/create.php",
            params={
                "format": "json",  # получаем ответ в формате JSON
                "url": long_url  # передаём длинную ссылку
            },
            timeout=10  # ждём ответа 10 секунд
        )

        # Превращаем ответ в словарь
        data = response.json()

        # Если есть короткая ссылка - возвращаем её
        if "shorturl" in data:
            return data["shorturl"]
        else:
            return "Ошибка: не удалось сократить ссылку"

    except Exception as e:
        return f"Ошибка: {str(e)}"


# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 "Привет! Я бот-сокращатель ссылок.\n\n"
                 "Просто отправь мне любую ссылку (например, https://google.com), "
                 "а я сделаю её короткой!"
                 )


# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message,
                 "Как пользоваться:\n"
                 "1. Скопируй длинную ссылку\n"
                 "2. Отправь её мне\n"
                 "3. Получи короткую ссылку\n\n"
                 "Пример: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                 )


# Обработка обычных сообщений (которые начинаются с http:// или https://)
@bot.message_handler(func=lambda message: message.text.startswith(('http://', 'https://')))
def handle_url(message):
    # Показываем, что бот "печатает"
    bot.send_chat_action(message.chat.id, 'typing')

    # Сокращаем ссылку
    short_url = shorten_url(message.text)

    # Отправляем результат
    bot.reply_to(message, f"Короткая ссылка: {short_url}")


# Если пользователь отправил не ссылку
@bot.message_handler(func=lambda message: True)
def handle_other(message):
    bot.reply_to(message,
                 "❌ Я не понял. Отправь мне ссылку, которая начинается с http:// или https://"
                 )


# Запускаем бота
print("Бот запущен и работает...")
bot.infinity_polling()