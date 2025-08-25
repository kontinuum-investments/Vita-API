from typing import List

from fastapi import APIRouter
from sirius import common
from sirius.common import DataClass
from sirius.communication.discord import Server, TextChannel, Bot

router = APIRouter()


class SendMessage(DataClass):
    message: str


@router.post(
    "/send_message",
    summary="Sends a message on Discord",
    description=f"Sends a message on Discord to the {common.get_environmental_secret("DISCORD_CHANNEL_NAME")} channel in the {common.get_environmental_secret("DISCORD_SERVER_NAME")} server.",
)
async def send_message(message: SendMessage) -> str:
    server_name: str = common.get_environmental_secret("DISCORD_SERVER_NAME")
    channel_name: str = common.get_environmental_secret("DISCORD_CHANNEL_NAME")
    bot: Bot = await Bot.get()
    server_list: List[Server] = await Server.get_all_servers(bot)
    server: Server = next(filter(lambda s: s.name == server_name, server_list))
    channel_list: List[TextChannel] = await TextChannel.get_all(server)
    channel: TextChannel = next(filter(lambda t: t.name == channel_name, channel_list))

    await channel.send_message(message.message)
    return "Message sent successfully."
