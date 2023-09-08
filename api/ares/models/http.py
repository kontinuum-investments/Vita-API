from sirius.common import DataClass


class Login(DataClass):
    application_name: str


class ConnectionInfo(DataClass):
    client_ip: str
    client_port: int
    server_fqdn: str
