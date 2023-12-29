from sirius import common

PORT_NUMBER: int = 8000
DEBUG_PORT_NUMBER: int = 9000
BASE_URL: str = f"http://localhost:{PORT_NUMBER}" if common.is_development_environment() else f"https://vita-api{'-test' if common.is_test_environment() else ''}.kih.com.sg"
ROUTE__ARES: str = "/ares"
ROUTE__ATHENA: str = "/athena"
ROUTE__CHRONOS: str = "/chronos"
ROUTE__HADES: str = "/hades"
ROUTE__HERMES: str = "/hermes"
