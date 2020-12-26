import logging
import os
import time
from json import JSONDecodeError
from pprint import pprint

import requests
import telegram
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG, filename='telegram_bot.log',
                    format='%(asctime)s %(name)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

HOMEWORK_STATUSES = {'reviewing': 'Работа взята в ревью!',
                     'rejected': 'К сожалению в работе нашлись ошибки.',
                     'approved': 'Ревьюеру всё понравилось, можно приступать к '
                                 'следующему уроку.'}


class WrongContentException(Exception):
    pass


def parse_homework_status(homework: dict) -> str:
    """
    Получить статус работы и вернуть статусное сообщение.

    Атрибуты функции
    ____________
    homework: dict
        Словарь с атрибутами домашней работы.
    """
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if not (homework_name and status):
        logger.error('Не удалось получить один из атрибутов домашней работы')
        raise WrongContentException()
    title = f'У вас проверили работу "{homework_name}"!\n\n'
    # title = f'Статус вашей домашней работы "{homework_name}" был изменен!\n\n'
    if status in HOMEWORK_STATUSES:
        return title + HOMEWORK_STATUSES[status]
    else:
        logger.warning(f'Работа получила неожиданный статус {status}')
        return title + f'Статус работы: {status}'


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
    try:
        homework_statuses = requests.get(
            'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
            headers=headers,
            params=data)
        return homework_statuses.json()
    except JSONDecodeError:
        logger.error('Сервис не доступен')


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
            homeworks = new_homework.get('homeworks')
            if homeworks:
                send_message(parse_homework_status(
                    homeworks[0]), bot_client)
                logger.info('Отправлено сообщение')
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(300)

        except Exception as e:
            logger.error(e, exc_info=True)
            time.sleep(5)


if __name__ == '__main__':
    main()
