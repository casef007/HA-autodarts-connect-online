"""Konstanten für die Autodarts Connect Online Integration."""

DOMAIN = "autodarts_connect"

# URLs für die Autodarts API
URL_CREDENTIALS = "http://login-darts-caller.peschi.org:3006/client-credentials"
URL_TOKEN = "https://login.autodarts.io/realms/autodarts/protocol/openid-connect/token"
URL_WEBSOCKET = "wss://api.autodarts.io/ms/v0/subscribe"
URL_REST_STATE = "https://api.autodarts.io/gs/v0/matches/{}/state"

# Globale Sensor-Namen
SENSOR_CURRENT_PLAYER = "Current Player"
SENSOR_GAME_MODE = "Game Mode"
SENSOR_BOARD_STATUS = "Board Status"