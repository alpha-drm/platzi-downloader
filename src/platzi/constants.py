from pathlib import Path

import platformdirs
from fake_useragent import UserAgent

APP_NAME = "Platzi"
SESSION_DIR = Path(platformdirs.user_data_dir(APP_NAME))
SESSION_FILE = SESSION_DIR / "state.json"  # Cookies are stored here

LOGIN_URL = "https://platzi.com/login"
LOGIN_DETAILS_URL = "https://api.platzi.com/api/v1/components/headerv2/user/"
URL_TOKEN = "https://platzi.com/api/v5/users/credentials/"

PLATZI_URL = "https://platzi.com"
REFERER = "https://platzi.com/"

ua = UserAgent()
HEADERS = {
    "User-Agent": ua.random,
    "Referer": f"{REFERER}",
    "Accept": "text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8,application/json",
    "Accept-Language": "es-ES, es;q=0.8, en-US;q=0.5, en;q=0.3",
    "Connection": "keep-alive",
    "Host": "mediastream.platzi.com",
    "Origin": f"{PLATZI_URL}",
}

# --- Session directory ---
SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

# --- Cache directory ---
CACHE_DIR = SESSION_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
