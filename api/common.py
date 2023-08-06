from enum import Enum

from sirius.communication.discord import Bot, TextChannel, Server

discord_bot: Bot | None = None
discord_server: Server | None = None


class DiscordTextChannel(Enum):
    NOTIFICATION: str = "notification"
    WISE: str = "wise"


class Discord:
    bot: Bot | None = None
    server: Server | None = None
    notification_channel: TextChannel | None = None

    @classmethod
    async def get_notification_channel(cls) -> TextChannel:
        if cls.notification_channel is not None:
            return cls.notification_channel

        cls.bot = await Bot.get()
        cls.server = await cls.bot.get_server()
        cls.notification_channel = await cls.server.get_text_channel(DiscordTextChannel.NOTIFICATION.value)
        return cls.notification_channel

    @classmethod
    async def notify(cls, message: str) -> None:
        await (await Discord.get_notification_channel()).send_message(message)
