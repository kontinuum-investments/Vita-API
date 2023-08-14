from sirius.common import DataClass


class Message(DataClass):
    message: str
    text_channel_name: str | None = None
