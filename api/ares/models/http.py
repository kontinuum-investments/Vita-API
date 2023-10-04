from sirius.common import DataClass


class ConnectionInfo(DataClass):
    client_ip: str
    client_port: int
    server_fqdn: str
