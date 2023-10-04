from sirius import common

BASE_URL: str = "http://localhost" if common.is_development_environment() else f"https://vita-api{'-test' if common.is_test_environment() else ''}.kih.com.sg"
ROUTE__ARES: str = "/ares"
ROUTE__ATHENA: str = "/athena"
ROUTE__CHRONOS: str = "/chronos"
ROUTE__HADES: str = "/hades"
ROUTE__HERMES: str = "/hermes"
