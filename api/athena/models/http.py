from sirius.common import DataClass


class Message(DataClass):
    text_channel_name: str
    message: str
