from enum import Enum

ROUTE__SEND_MESSAGE: str = "/send_message"
ROUTE__SEND_NOTIFICATION_MESSAGE: str = "/send_notification_message"
ROUTE__DISCORD__RECEIVE_MESSAGE: str = "/discord_receive_message"
ROUTE__TEST_WEBHOOK: str = "/test_webhook"


class DiscordTextChannel(Enum):
    NOTIFICATION: str = "notification"
    WISE: str = "wise"
    HOUSEHOLD_FINANCES: str = "household-finances"
    LOGS: str = "logs"
