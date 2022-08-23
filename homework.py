"""The main module of the Telegram bot."""

import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s - %(name)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
stream_handler.setFormatter(formatter)
stream_handler.addFilter(logging.Filter(__name__))

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
TIME_OFFSET = 10801

ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

previous_bot_message = ""


def send_message(bot, message):
    """Sending a message to Telegram chat."""
    global previous_bot_message
    if previous_bot_message != message:
        try:
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
            )
        except Exception as error:
            logger.error(f"Error sending message from bot: '{error}'")
        else:
            logger.info(f"Bot sent a message: '{message}'")
            previous_bot_message = message


def get_api_answer(current_timestamp):
    """API service endpoint request."""
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != 200:
        raise Exception(
            f"Status code of endpoint '{ENDPOINT}' does not match OK."
        )
    return homework_statuses.json()


def check_response(response):
    """Checking the service API response for correctness."""
    if isinstance(response, list):
        response = response[0]
    if not isinstance(response, dict):
        raise Exception(
            "The API response cast to Python data types is unexpected."
        )
    try:
        homeworks = response["homeworks"]
    except KeyError:
        Exception("The API response is missing homework information.")
    if not isinstance(homeworks, list):
        raise Exception("The data type in the API response is unexpected.")
    if not homeworks:
        logger.debug(
            "The API response does not contain information about homeworks."
        )
    return homeworks


def parse_status(homework):
    """Get homework status."""
    homework_status = homework.get("status")
    if not homework_status:
        raise Exception("No homework status found in API response.")
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError:
        Exception(
            "Undocumented homework status was found in the API response."
        )
    try:
        homework_name = homework["homework_name"]
    except KeyError:
        Exception("No homework title found in API response.")
    try:
        homework_name = homework["homework_name"]
    except ValueError:
        Exception("No homework title found in API response.")
    if not homework_name:
        raise Exception("No homework title found in API response.")

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Checking the availability of environment variables."""
    return (
        bool(PRACTICUM_TOKEN)
        and bool(TELEGRAM_TOKEN)
        and bool(TELEGRAM_CHAT_ID)
    )


def main():
    """The main logic of the bot."""
    if not check_tokens():
        logger.critical(
            "Missing required environment variable(s) during bot startup.",
            exc_info=True,
        )
        exit("The program has been forcibly stopped.")
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                current_homework = homeworks[-1]
                message = parse_status(current_homework)
                send_message(bot, message)
                date_homework = current_homework.get("date_updated")
                current_timestamp = (
                    int(
                        time.mktime(
                            time.strptime(date_homework, "%Y-%m-%dT%H:%M:%SZ")
                        )
                    )
                    + TIME_OFFSET
                )
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f"Program crash: {error}"
            logger.error(message, exc_info=True)
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    main()
