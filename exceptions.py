"""Custom exceptions."""


class InvalidJSON(Exception):
    """Error converting JSON to Python data type."""


class TelegramSendMessageError(Exception):
    """Error sending message to Telegram."""


class RequestError(Exception):
    """API request failed."""


class HTTPStatusNotOK(Exception):
    """Response status code is not OK."""


class ResponseNoHomework(Exception):
    """Homework is not in the API response."""


class DebugInfo(Exception):
    """Debugging information."""


class HomeworkNoNewInformation(DebugInfo):
    """API response does not contain new information about homeworks."""


class NoResponseTime(DebugInfo):
    """API response is missing response time."""
