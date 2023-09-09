from enum import Enum

ROUTE__SEND_MESSAGE: str = "/send_message"
ROUTE__SEND_NOTIFICATION_MESSAGE: str = "/send_notification_message"


class DiscordTextChannel(Enum):
    NOTIFICATION: str = "notification"
    WISE: str = "wise"
