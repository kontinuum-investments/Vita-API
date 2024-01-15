import discord
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from sirius import common
from sirius.ai.large_language_model import LargeLanguageModel, Conversation
from sirius.common import threaded
from sirius.communication.discord import Bot, Server, TextChannel, Message
from sirius.constants import EnvironmentSecret
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.athena.constants import DiscordTextChannel

client: discord.Client = discord.Client(intents=discord.Intents.default())


@client.event
async def on_ready() -> None:
    #   TODO: Does not work
    # asyncio.ensure_future(Logger.debug("Athena's Discord client started up successfully"))
    pass


@client.event
async def on_message(discord_message: discord.message.Message) -> None:
    if discord_message.author == client.user:
        return

    message: Message = Message.get(discord_message)
    conversation: Conversation = Conversation.get_conversation(LargeLanguageModel.GPT4_TURBO)

    try:
        reply: str = await conversation.say(f"You are a helpful assistant named \"Athena\". You will try to answer all queries in Markdown syntax where it is appropriate.\n"
                                            f"Query: {message.content}")
        await discord_message.channel.send(reply, reference=discord_message)
    except Exception as e:
        exception_message: str = str(e)
        reply = await conversation.say(f"You are a helpful assistant named \"Athena\". You will try to answer all queries in Markdown syntax where it is appropriate. Your job is to give an explanation on a given Python error message\n"
                                       f"Query: The python error message is: {exception_message}")
        await discord_message.channel.send(f"Ran into an error when trying to answer the query: ```{exception_message}```\n\n"
                                           f"The cause of the error might be: {reply}", reference=discord_message)


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
    async def notify_error(error_location: str, message: str) -> None:
        await Discord.send_message(DiscordTextChannel.NOTIFICATION, f"**Error in _{error_location}_**\n{message}")

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

    @staticmethod
    @threaded
    def start_discord_client() -> None:
        global client
        client.run(common.get_environmental_secret(EnvironmentSecret.DISCORD_BOT_TOKEN))
