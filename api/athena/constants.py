from enum import Enum

ROUTE__SEND_MESSAGE: str = "/send_message"


class DiscordTextChannel(Enum):
    NOTIFICATION: str = "notification"
    WISE: str = "wise"
