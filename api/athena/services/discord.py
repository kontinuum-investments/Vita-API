from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from sirius.communication.discord import Bot, Server, TextChannel
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.athena.constants import DiscordTextChannel


class Discord:
    bot: Bot | None = None
    server: Server | None = None
    notification_channel: TextChannel | None = None

    @classmethod
    async def _initialize(cls) -> None:
        cls.bot = await Bot.get() if cls.bot is None else cls.bot
        cls.server = await cls.bot.get_server() if cls.server is None else cls.server

    @classmethod
    async def send_message(cls, discord_text_channel: DiscordTextChannel, message: str) -> None:
        await cls._initialize()
        text_channel: TextChannel = await cls.server.get_text_channel(discord_text_channel.value)
        await text_channel.send_message(message)

    @staticmethod
    async def notify(message: str) -> None:
        await Discord.send_message(DiscordTextChannel.NOTIFICATION, message)

    @staticmethod
    async def handle_receive_message(request: Request) -> JSONResponse:
        verify_key: VerifyKey = VerifyKey(bytes.fromhex("32928a064573dbede1d8641d80d9aa512226da9c74835e232f17745f55fe021d"))
        signature: str = request.headers["X-Signature-Ed25519"]
        timestamp: str = request.headers["X-Signature-Timestamp"]
        body: str = (await request.body()).decode("utf-8")

        try:
            verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
        except BadSignatureError:
            return JSONResponse(None, status_code=401)

        return JSONResponse({"type": 1}, status_code=200)
