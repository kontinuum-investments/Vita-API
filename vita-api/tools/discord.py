import base64
from typing import List

from fastapi import APIRouter, Response, status
from sirius import common
from sirius.common import DataClass
from sirius.communication.discord import Server, TextChannel, Bot, DiscordMedia

router = APIRouter()


class Media(DataClass):
    media_base64: str
    file_extension: str


class SendMessage(DataClass):
    message: str
    media_list: List[Media] | None = []


@router.post("/send_message", summary="Sends a message on Discord")
async def send_message(message: SendMessage) -> Response:
    server_name: str = common.get_environmental_secret("DISCORD_SERVER_NAME")
    channel_name: str = common.get_environmental_secret("DISCORD_CHANNEL_NAME")
    bot: Bot = await Bot.get()
    server_list: List[Server] = await Server.get_all_servers(bot)
    server: Server = next(filter(lambda s: s.name == server_name, server_list))
    channel_list: List[TextChannel] = await TextChannel.get_all(server)
    channel: TextChannel = next(filter(lambda t: t.name == channel_name, channel_list))
    media_list: List[DiscordMedia] = [DiscordMedia(media=base64.b64decode(media.media_base64), file_extension=media.file_extension) for media in message.media_list]

    channel.send_message(message.message, media_list=media_list)
    return Response(status_code=status.HTTP_200_OK)
