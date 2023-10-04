from api import constants
from api.constants import ROUTE__ARES

ROUTE__GET_ACCESS_TOKEN_REMOTELY: str = "/access_token_remotely"
ROUTE__ENTRA_ID_LOGIN_URL: str = "/entra_id_login_url"
ROUTE__ENTRA_ID_ACCESS_TOKEN_FROM_AUTHENTICATION_CODE: str = "/entra_id_access_token_from_authentication_code"
ROUTE__ENTRA_ID_RESPONSE: str = "/entra_id_response"
ROUTE__IS_ACCESS_TOKEN_VALID: str = "/is_access_token_valid"
ROUTE__GET_CURRENT_USER: str = "/current_user"
ROUTE__GET_CONNECTION_INFO: str = "/connection_info"
MICROSOFT_ENTRA_ID_DEFAULT_AUTHENTICATION_REDIRECT_URL: str = f"{constants.BASE_URL}{ROUTE__ARES}{ROUTE__ENTRA_ID_RESPONSE}"
