"""Main module of Telegram bot."""

import logging
import os
import sys
import time
from http import HTTPStatus
from json import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException

import exceptions

load_dotenv(override=True)

logger = logging.getLogger(__name__)

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600

ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def logging_settings() -> None:
    """Logging settings."""
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s "
        "[%(name)s] %(filename)s - %(lineno)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(logging.Filter(__name__))
    logger.addHandler(stream_handler)


def send_message(bot: telegram.Bot, message: str) -> None:
    """Sending a message to Telegram chat."""
    logger.info(f"Bot sends a message: '{message}'")
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except telegram.TelegramError as error:
        raise exceptions.TelegramSendMessageError(
            f"Error sending message from bot: {error}"
        )
    else:
        logger.info(f"Bot sent a message: '{message}'")


def get_api_answer(current_timestamp: int) -> dict:
    """API service endpoint request."""
    logger.info("Endpoint request.")
    params = {"from_date": current_timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except RequestException as error:
        raise exceptions.RequestError(f"API request failed: {error}")
    if homework_statuses.status_code != HTTPStatus.OK:
        raise exceptions.HTTPStatusNotOK(
            f"Status code of API response is not OK: "
            f"{homework_statuses.status_code}. Endpoint: {ENDPOINT}"
        )
    try:
        return homework_statuses.json()
    except JSONDecodeError:
        raise exceptions.InvalidJSON(
            f"API response contains invalid JSON: {homework_statuses}"
        )


def check_response(response: dict) -> list:
    """Checking service API response for correctness."""
    logger.info("Checking the API response for correctness.")
    if not isinstance(response, dict):
        raise TypeError(
            f"API response cast to Python data types "
            f"is unexpected: {response}"
        )
    if "homeworks" not in response:
        raise exceptions.ResponseNoHomework(
            f"API response is missing homework information: {response}"
        )
    if "current_date" not in response:
        raise exceptions.NoResponseTime(
            f"API response is missing response time: {response}"
        )
    homeworks = response["homeworks"]
    if not isinstance(homeworks, list):
        raise TypeError(f"Data type in API response is unexpected: {response}")
    if not homeworks:
        raise exceptions.HomeworkNoNewInformation(
            f"API response does not contain new information "
            f"about homeworks: {response}"
        )
    return homeworks


def parse_status(homework: dict) -> str:
    """Get homework status."""
    logger.info("Getting homework status.")
    homework_status = homework.get("status")
    if not homework_status:
        raise KeyError(f"No homework status found in API response: {homework}")
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if not verdict:
        raise KeyError(
            f"Undocumented homework status was found in API response: "
            f"{homework}"
        )
    homework_name = homework.get("homework_name")
    if not homework_name:
        raise KeyError(f"No homework title found in API response: {homework}")
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Checking availability of environment variables."""
    logger.info("Checking the availability of environment variables.")
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main() -> None:
    """Main logic of bot."""
    if not check_tokens():
        message = (
            f"Missing required environment variable(s) during bot startup. "
            f"PRACTICUM_TOKEN = {PRACTICUM_TOKEN}, "
            f"TELEGRAM_TOKEN = {TELEGRAM_TOKEN}, "
            f"TELEGRAM_CHAT_ID = {TELEGRAM_CHAT_ID}, "
        )
        logger.critical(message, exc_info=True)
        exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    previous_bot_message = ""
    current_timestamp = 0
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            current_homework = homeworks[0]
            message = parse_status(current_homework)
            logger.info(message)
            if previous_bot_message != message:
                send_message(bot, message)
                previous_bot_message = message
                current_timestamp = response.get("current_date")
        except exceptions.TelegramSendMessageError as error:
            logger.error(f"Program crash: {error}", exc_info=True)
        except exceptions.DebugInfo as error:
            logger.debug(error)
        except Exception as error:
            message = f"Program crash: {error}"
            logger.error(message, exc_info=True)
            if previous_bot_message != message:
                send_message(bot, message)
                previous_bot_message = message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    logging_settings()
    try:
        logger.info("The bot has started.")
        main()
    except KeyboardInterrupt:
        logger.info("The bot has completed its work.")
