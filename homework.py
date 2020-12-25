import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG, filename='telegram_bot.log',
                    format='%(asctime)s %(name)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def parse_homework_status(homework: dict) -> str:
    """
    Получить статус работы и вернуть статусное сообщение.

    Атрибуты функции
    ____________
    homework: dict
        Словарь с атрибутами домашней работы.
    """
    homework_name = homework.get('homework_name')
    if homework.get('status') == 'reviewing':
        return f'Работа "{homework_name}" взята в ревью!'
    if homework.get('status') == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = ('Ревьюеру всё понравилось, можно приступать к следующему '
                   'уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp: int) -> dict:
    """
    Отправить запрос об изменении статусов с указанного периода времени к
    ЯПрактикуму и вернуть ответ сервера.

    Атрибуты функции
    ____________
    current_timestamp: int
        Точка времени начиная с которой выбираются сообщения. Формат Unix time.
    """
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
    data = {
        'from_date': current_timestamp
    }
    homework_statuses = requests.get(
        'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        headers=headers,
        params=data)
    return homework_statuses.json()


def send_message(message: str, bot_client: telegram.Bot) -> telegram.Message:
    """
    Отправить сообщение в чат бота.

    Атрибуты функции
    ____________
    message: str
        Текст отправляемого сообщения
    bot_client: telegram.Bot
        Клиент для отправки сообщения
    """
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main() -> None:
    """
    Опрашивать на наличие обновлений ЯПрактикум, в случае появления нового
    статуса, отсылать статусное сообщение в чат телеграм-бота.
    """
    logger.debug('Запуск бота')
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot_client)
                logger.info('Отправлено сообщение')
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(300)

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            logger.error(e, exc_info=True)
            time.sleep(5)


if __name__ == '__main__':
    main()
