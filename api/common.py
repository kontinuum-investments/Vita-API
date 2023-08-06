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
    async def send_message(cls, discord_text_channel: DiscordTextChannel, message: str) -> None:
        cls.bot = await Bot.get() if cls.bot is None else cls.bot
        cls.server = await cls.bot.get_server() if cls.server is None else cls.server
        text_channel: TextChannel = await cls.server.get_text_channel(discord_text_channel.value)
        await text_channel.send_message(message)

    @classmethod
    async def notify(cls, message: str) -> None:
        await Discord.send_message(DiscordTextChannel.NOTIFICATION, message)
